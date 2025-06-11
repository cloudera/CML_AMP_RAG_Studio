#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2025
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#  NOTE: Cloudera open source products are modular software products
#  made up of hundreds of individual components, each of which was
#  individually copyrighted.  Each Cloudera open source product is a
#  collective work under U.S. Copyright Law. Your license to use the
#  collective work is as provided in your written agreement with
#  Cloudera.  Used apart from the collective work, this file is
#  licensed for your use pursuant to the open source license
#  identified above.
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
#  contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
#  KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
#  WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
#  IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
#  AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
#  ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
#  OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
#  CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
#  RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
#  BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
#  DATA.
#
import json
import logging
import os
from queue import Queue
from typing import Optional, Tuple, Any, Generator

import opik
from crewai import Task, Process, Crew, Agent, CrewOutput, TaskOutput
from llama_index.agent.openai import OpenAIAgent
from llama_index.core import PromptTemplate
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.llms.types import ChatMessage, MessageRole, ChatResponse
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from llama_index.core.llms import LLM
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.schema import NodeWithScore
from llama_index.core.tools import BaseTool, ToolOutput

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.services.query.agents.models import get_crewai_llm_object_direct
from app.services.query.chat_engine import (
    FlexibleContextChatEngine,
)
from app.services.query.crew_events import ChatEvents, step_callback
from app.services.query.query_configuration import QueryConfiguration
from app.services.query.tasks.calculation import build_calculation_task
from app.services.query.tasks.date import build_date_task
from app.services.query.tasks.retriever import build_retriever_task
from app.services.query.tools.date import DateTool
from app.services.query.tools.retriever import (
    build_retriever_tool,
)

if os.environ.get("ENABLE_OPIK") == "True":
    from opik.integrations.crewai import track_crewai

    opik.configure(
        use_local=True, url=os.environ.get("OPIK_URL", "http://localhost:5174")
    )

logger = logging.getLogger(__name__)
# litellm._turn_on_debug()
poison_pill = "poison_pill"


def validate_with_context(result: TaskOutput) -> Tuple[bool, Any]:
    try:
        return True, result
    except Exception as e:
        print(f"Validation failed: {e}")
        return False, str(e)


def should_use_retrieval(
    configuration: QueryConfiguration,
    data_source_ids: list[int],
    llm: LLM,
    query_str: str,
    chat_messages: list[ChatMessage],
) -> tuple[bool, dict[int, str]]:

    data_source_summaries: dict[int, str] = {}
    for data_source_id in data_source_ids:
        data_source_summary_indexer = SummaryIndexer.get_summary_indexer(data_source_id)
        if data_source_summary_indexer:
            data_source_summary = data_source_summary_indexer.get_full_summary()
            data_source_summaries[data_source_id] = data_source_summary
    # Create a planner agent to decide whether to use retrieval or answer directly
    # planner = PlannerAgent(llm, configuration)
    # planning_decision = planner.decide_retrieval_strategy(
    #     query_str, chat_messages, data_source_summaries
    # )
    # use_retrieval: bool = planning_decision.get("use_retrieval", True)
    return len(data_source_ids) > 0, data_source_summaries


def assemble_crew(
    use_retrieval: bool,
    llm: LLM,
    chat_messages: list[ChatMessage],
    query_str: str,
    crew_events_queue: Queue[ChatEvents],
    retriever: Optional[BaseRetriever],
    data_source_summaries: dict[int, str],
    mcp_tools: Optional[list[BaseTool]] = None,
) -> Crew:
    crewai_llm = get_crewai_llm_object_direct(llm, getattr(llm, "model", ""))
    # Gather all the tools needed for the crew

    # Create a date tool to get the current date and time
    date_tool = DateTool()
    research_tools: list[BaseTool] = [date_tool]

    # Create a retriever tool if needed
    crewai_retriever_tool = None
    if use_retrieval and retriever:
        logger.info("Planner decided to use retrieval")
        crewai_retriever_tool = build_retriever_tool(retriever, data_source_summaries)
        research_tools.append(crewai_retriever_tool)

    # Define the researcher agent
    researcher = Agent(
        role="Researcher",
        goal=f"Research and find relevant information about `{query_str}` and provide comprehensive research insights.",
        backstory="You are an expert researcher who provides accurate and relevant information. "
        "You know when to use tools and when to answer directly.",
        llm=crewai_llm,
        verbose=True,
        step_callback=lambda output: step_callback(
            output, "Tool Result", crew_events_queue
        ),
        max_execution_time=120,
        max_iter=15,
        max_rpm=10,
        max_retry_limit=5,
    )

    # Define tasks for the researcher agents
    date_task = build_date_task(researcher, date_tool, crew_events_queue)

    crew_events_queue.put(
        ChatEvents(
            type="chat_history",
            name="Providing chat history",
            data=f"<Chat History>:\n{query_str}",
        )
    )
    chat_history = ""
    if chat_messages:
        for message in chat_messages:
            if message.role == MessageRole.USER:
                chat_history += f"User:\n{message.content}\n"
            elif message.role == MessageRole.ASSISTANT:
                chat_history += f"Assistant:\n{message.content}\n"

        crew_events_queue.put(
            ChatEvents(
                type="chat_history",
                name="Chat history provided",
                data=chat_history,
            )
        )
    else:
        crew_events_queue.put(
            ChatEvents(
                type="chat_history",
                name="Chat history empty",
                data="<Chat History>:\nNo chat history available.",
            )
        )

    # create a list of tasks for the researcher
    researcher_task_context = [date_task]

    # Add retriever task if needed
    if crewai_retriever_tool:
        retriever_task_context = [date_task]
        retriever_task = build_retriever_task(
            researcher,
            query_str,
            chat_history,
            retriever_task_context,
            crewai_retriever_tool,
            crew_events_queue,
        )
        researcher_task_context.append(retriever_task)

    research_task = Task(
        name="ResearcherTask",
        description="Research the user's question using the context available, "
        "chat history, and the tools provided. Note that the date provided in the context is the current date. "
        "Based on that, research and return comprehensive insights. If the answer is not available in the "
        "context or chat history, use the tools to gather information. "
        "No need to use the tools if the answer is available in the context or chat history. \n"
        "Given below, is the user's question and the chat history: \n\n"
        f"<Chat History>:\n{chat_history}\n\n"
        f"<Question>:\n{query_str}",
        agent=researcher,
        expected_output="A detailed analysis of the user's question based on the provided context and chat history, "
        "including relevant links and in-line citations."
        "Note for in-line citations: \n"
        "* Use the citations from the chat history as is. "
        "* Use links and results from the search if needed to answer the question "
        "and cite them in-line in the given format: the link should be in markdown format. For example: "
        "Refer to the example in [example.com](https://example.com). Do not make up links that are not "
        "present chat history or context.\n"
        "* Cite from retriever results (retriever_results) in the given format: the node_id "
        "should be in an html anchor tag (<a href>) with an html 'class' of 'rag_citation'. "
        "Do not use filenames as citations. Only node ids should be used."
        "For example: <a class='rag_citation' href='2'>2</a>. Do not make up node ids that are not present "
        "in the context.\n"
        "* All citations should be either in-line citations or markdown links. \n"
        "* If there are no retriever results, do not use any citations from the retriever results. ",
        context=researcher_task_context,
        callback=lambda output: step_callback(
            output, "Research Complete", crew_events_queue
        ),
        tools=mcp_tools,
        max_retries=5,
        guardrail=validate_with_context,
    )

    # Create a calculation task if needed
    calculation_task_context = [research_task]
    calculation_task = build_calculation_task(
        researcher, calculation_task_context, crew_events_queue
    )

    # Create a responder agent that formulates the final response
    responder = Agent(
        role="Responder",
        goal=f"Provide a comprehensive and accurate response to the user's question. \n<Question>\n: {query_str}",
        backstory="You are an expert at formulating clear, concise, and accurate responses based on research findings.",
        llm=crewai_llm,
        step_callback=lambda output: step_callback(
            output, "Response Computed", crew_events_queue
        ),
        verbose=True,
        max_execution_time=120,
        max_iter=15,
        max_rpm=10,
        max_retry_limit=5,
    )

    response_context = [research_task, calculation_task]

    response_task = Task(
        name="ResponderTask",
        description="Formulate a comprehensive response based on the research findings and calculations, "
        "including any relevant links and in-line citations.",
        agent=responder,
        expected_output="A accurate response to the user's question. The links and citations are to be copied as is "
        "from the context. Do not format it, or change it in any way.",
        context=response_context,
        callback=lambda _: crew_events_queue.put(
            ChatEvents(type=poison_pill, name="responder")
        ),
        max_retries=3,
        guardrail=validate_with_context,
    )

    # Create a crew with the agents and tasks
    agents = []
    tasks = []

    for task in researcher_task_context:
        tasks.append(task)
    agents.extend([researcher, responder])
    tasks.extend(
        [
            research_task,
            calculation_task,
            response_task,
        ]
    )

    if os.environ.get("ENABLE_OPIK") == "True":
        track_crewai(project_name="crewai-ragstudio")

    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        name="QueryCrew",
        prompt_file="app/services/query/agents/override_prompts.json",
    )


def launch_crew(
    crew: Crew,
    query_str: str,
) -> Tuple[str, CrewOutput]:
    # Run the crew to get the enhanced response
    try:
        crew_result: CrewOutput = crew.kickoff()

        # Create an enhanced query that includes the CrewAI insights
        return (
            f"""
    Original query: {query_str}
    
    Research insights: {crew_result}
    
    Please provide a response to the original query, incorporating the insights from research with in-line citations. \
    
    Adhere to the following guidelines:
    * If you cannot find relevant information in the research insights, answer the question directly and indicate that \
    you don't have enough information. 
    * If citations from the research insights are used, use the in-line links and \
    citations from the research insights as is. Keep markdown formatted links as is i.e. [<text>](<web_link>). \
    Keep the in-line citations of format `<a class='rag_citation' href='node_id'>node_id</a>` as is. 
    * Do not make up any links or citations of the form `<a class='rag_citation' href='node_id'>node_id</a>` \
    that are not present in the research insights. Do not make up any markdown links as well. Only use the \
    links and citations from the research insights. 
    """,
            crew_result,
        )
    except Exception as e:
        logger.exception("Error running CrewAI crew")
        raise RuntimeError("Error running CrewAI crew: %s" % str(e)) from e


DEFAULT_AGENT_PROMPT = """\
You are an expert agent that can answer questions with the help of tools. \
If you do not know the answer to a question, you truthfully say \
it does not know.

As the agent, you will provide an answer based solely on the provided sources with \
citations to the paragraphs. When referencing information from a source, \
cite the appropriate source(s) using their corresponding ids. \
Every answer/paragraph should include at least one source citation. \
Only cite a source when you are explicitly referencing it. \
The citations with node_ids should be the href of an anchor tag \
(<a class="rag_citation" href=CITATION_HERE></a>), \
and (IMPORTANT) in-line with the text. No footnotes or endnotes. \
If none of the sources are helpful, you should indicate that. \
Do not make up source ids for citations. 

Note for in-line citations:
* Use the citations from the chat history as is. 
* Use links if needed to answer the question and cite them in-line \
in the given format: the link should be in markdown format. For example: \
Refer to the example in [example.com](https://example.com). Do not make up links that are not \
present. 
* Cite from nodes in the given format: the node_id \
should be in an html anchor tag (<a href>) with an html 'class' of 'rag_citation'. \
Do not use filenames as citations. Only node ids should be used. \
For example: <a class='rag_citation' href='2'>2</a>. Do not make up node ids that are not present 
in the context.
* All citations should be either in-line citations or markdown links. 

For example:

<Contexts>
Source: 1
The sky is red in the evening and blue in the morning.

Source: 2
Water is wet when the sky is red.

Source: www.example.com
The sky is red in the evening and blue in the morning. 

<Query>
When is water wet?

<Answer> 
Water will be wet when the sky is red<a class="rag_citation" href="1"></a> \
[example.com](www.example.com), which occurs in the evening<a class="rag_citation" href="2"></a>.
"""


def stream_chat(
    use_retrieval: bool,
    llm: FunctionCallingLLM,
    chat_engine: Optional[FlexibleContextChatEngine],
    enhanced_query: str,
    chat_messages: list[ChatMessage],
    additional_tools: list[BaseTool],
    data_source_summaries: dict[int, str],
) -> StreamingAgentChatResponse:
    # Use the existing chat engine with the enhanced query for streaming response
    chat_response: StreamingAgentChatResponse

    if use_retrieval and chat_engine:
        retrieval_tool = build_retriever_tool(
            retriever=chat_engine._retriever,
            summaries=data_source_summaries,
            node_postprocessors=chat_engine._node_postprocessors,
        )
        tools: list[BaseTool] = [DateTool(), retrieval_tool]
        tools.extend(additional_tools)
        agent = OpenAIAgent.from_tools(
            tools=tools,
            llm=llm,
            verbose=True,
            system_prompt=DEFAULT_AGENT_PROMPT,
        )

        stream_chat_response: StreamingAgentChatResponse = agent.stream_chat(
            message=enhanced_query, chat_history=chat_messages
        )

        def gen() -> Generator[ChatResponse, None, None]:
            response = ""
            res = stream_chat_response.response_gen
            for chunk in res:
                response += chunk
                finalize_response = ChatResponse(
                    message=ChatMessage(role="assistant", content=response), delta=chunk
                )
                yield finalize_response

        source_nodes = []
        if stream_chat_response.sources:
            for tool_output in stream_chat_response.sources:
                if isinstance(tool_output, ToolOutput):
                    if (
                        tool_output.raw_output
                        and isinstance(tool_output.raw_output, list)
                        and all(
                            isinstance(elem, NodeWithScore)
                            for elem in tool_output.raw_output
                        )
                    ):
                        source_nodes.extend(tool_output.raw_output)

        return StreamingAgentChatResponse(chat_stream=gen(), source_nodes=source_nodes)
    else:
        # If the planner decides to answer directly, bypass retrieval
        logger.debug("Planner decided to answer directly without retrieval")
        logger.debug("querying llm directly with enhanced query: \n%s", enhanced_query)

        # Use the chat engine to answer directly without retrieval context
        return StreamingAgentChatResponse(
            chat_stream=llm.stream_chat(
                messages=chat_messages
                + [ChatMessage(role="user", content=enhanced_query)],
            ),
            sources=[],
            source_nodes=[],
            is_writing_to_memory=False,
        )
