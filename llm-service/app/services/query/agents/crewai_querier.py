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
import logging
import os
import time
from queue import Queue
from typing import Optional

import opik
from crewai import Task, Process, Crew, Agent, CrewOutput
from crewai.agents.parser import AgentFinish
from crewai.tools.base_tool import BaseTool
from crewai.tools.tool_types import ToolResult
from crewai_tools import SerperDevTool
from crewai_tools.tools.llamaindex_tool.llamaindex_tool import LlamaIndexTool
from llama_index.core import QueryBundle, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from llama_index.core.llms import LLM
from llama_index.core.tools import RetrieverTool, ToolMetadata
from pydantic import BaseModel

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.services.query.agents.date_tool import DateTool
from app.services.query.agents.models import get_crewai_llm_object_direct
from app.services.query.agents.planner_agent import PlannerAgent
from app.services.query.chat_engine import (
    FlexibleContextChatEngine,
)
from app.services.query.flexible_retriever import FlexibleRetriever
from app.services.query.query_configuration import QueryConfiguration

if os.environ.get("ENABLE_OPIK") == "True":
    from opik.integrations.crewai import track_crewai

    opik.configure(
        use_local=True, url=os.environ.get("OPIK_URL", "http://localhost:5174")
    )

logger = logging.getLogger(__name__)

poison_pill = "poison_pill"


class CrewEvent(BaseModel):
    type: str
    name: str
    data: Optional[str] = None
    timestamp: float = time.time()


def step_callback(
    output: ToolResult | AgentFinish, agent: str, crew_events_queue: Queue[CrewEvent]
) -> None:
    if isinstance(output, AgentFinish):
        crew_events_queue.put(
            CrewEvent(
                type="agent_finish",
                name=agent,
                data=output.thought,
                timestamp=time.time(),
            )
        )


def build_calculation_task(agent: Agent, crew_events_queue: Queue[CrewEvent]) -> Task:
    calculation_task = Task(
        name="CalculatorTask",
        description="Perform any necessary calculations based on the research findings. If the query requires numerical analysis, perform the calculations and show your work. If no calculations are needed, simply state that no calculations are required.",
        agent=agent,
        expected_output="Results of any calculations performed, with step-by-step workings",
        # callback=lambda output: step_callback(
        #     output, "Calculation Complete", crew_events_queue
        # ),
    )
    return calculation_task


class SearchResult(BaseModel):
    result: str
    link: str


class SearchOutput(BaseModel):
    results: list[SearchResult]


def build_search_task(
    agent: Agent,
    query: str,
    date_tool: DateTool,
    search_tool: SerperDevTool,
    crew_events_queue: Queue[CrewEvent],
) -> Task:
    search_task = Task(
        name="SearchTask",
        description=f"Search the internet for relevant information related to the user's question.  User's question: {query}.",
        agent=agent,
        tools=[date_tool, search_tool],
        expected_output="Results of any search performed, with step-by-step workings, including links to the sources.",
        output_json=SearchOutput,
        # callback=lambda output: step_callback(
        #     output, "Search Complete", crew_events_queue
        # ),
    )
    return search_task


class RetrieverResult(BaseModel):
    node_id: str
    content: str


class RetrieverOutput(BaseModel):
    results: list[RetrieverResult]


def build_retriever_task(
    agent: Agent,
    query: str,
    retriever_tool: BaseTool,
    crew_events_queue: Queue[CrewEvent],
) -> Task:
    retriever_task = Task(
        name="RetrieverTask",
        description="Retrieve relevant information from the index based the user's question: \n\n"
        f"<Question>:\n{query}.",
        agent=agent,
        tools=[retriever_tool],
        expected_output="Relevant information retrieved from the index, including links to the sources.",
        output_json=RetrieverOutput,
        # callback=lambda output: step_callback(
        #     output, "Retrieval Complete", crew_events_queue
        # ),
    )
    return retriever_task


def build_date_task(
    agent: Agent, date_tool: DateTool, crew_events_queue: Queue[CrewEvent]
) -> Task:
    date_task = Task(
        name="DateFinderTask",
        description="Find the current date and time.",
        agent=agent,
        expected_output="The current date and time.",
        tools=[date_tool],
        # callback=lambda output: step_callback(output, "Date Found", crew_events_queue),
    )
    return date_task


def should_use_retrieval(
    configuration: QueryConfiguration,
    data_source_id: Optional[int],
    llm: LLM,
    query_str: str,
    chat_messages: list[ChatMessage],
) -> bool:
    if not data_source_id:
        return False

    data_source_summary_indexer = SummaryIndexer.get_summary_indexer(data_source_id)
    data_source_summary = None
    if data_source_summary_indexer:
        data_source_summary = data_source_summary_indexer.get_full_summary()
    # Create a planner agent to decide whether to use retrieval or answer directly
    planner = PlannerAgent(llm, configuration)
    planning_decision = planner.decide_retrieval_strategy(
        query_str, chat_messages, data_source_summary
    )
    use_retrieval: bool = planning_decision.get("use_retrieval", True)
    return use_retrieval


def assemble_crew(
    use_retrieval: bool,
    llm: LLM,
    embedding_model: Optional[BaseEmbedding],
    chat_messages: list[ChatMessage],
    index: Optional[VectorStoreIndex],
    query_str: str,
    configuration: QueryConfiguration,
    data_source_id: Optional[int],
    crew_events_queue: Queue[CrewEvent],
) -> Crew:
    crewai_llm = get_crewai_llm_object_direct(llm, configuration.model_name)
    # Gather all the tools needed for the crew

    # Create a date tool to get the current date and time
    date_tool = DateTool()
    research_tools: list[BaseTool] = [date_tool]

    # Create a search tool if needed
    search_tool = None
    if configuration.tools and "search" in configuration.tools:
        search_tool = SerperDevTool()
        research_tools.append(search_tool)

    # Create a retriever tool if needed
    crewai_retriever_tool = None
    if use_retrieval and index and embedding_model and data_source_id:
        logger.info("Planner decided to use retrieval")

        # First, get the context from the retriever
        # TODO: Make a retriever tool and task
        base_retriever = FlexibleRetriever(
            configuration=configuration,
            index=index,
            embedding_model=embedding_model,
            data_source_id=data_source_id,
            llm=llm,
        )
        # fetch summary fromm index if available
        data_source_summary_indexer = SummaryIndexer.get_summary_indexer(data_source_id)
        data_source_summary = None
        if data_source_summary_indexer:
            data_source_summary = data_source_summary_indexer.get_full_summary()
        retriever_tool = RetrieverTool.from_defaults(
            retriever=base_retriever,
            name="Retriever",
            description=(
                "A tool to retrieve relevant information from "
                "the index. "
                f"The index information about: {data_source_summary}"
                if data_source_summary
                else ""
            ),
        )
        crewai_retriever_tool = LlamaIndexTool.from_tool(retriever_tool)
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
            output, "Research Complete", crew_events_queue
        ),
    )

    # Define tasks for the researcher agents
    date_task = build_date_task(researcher, date_tool, crew_events_queue)
    calculation_task = build_calculation_task(researcher, crew_events_queue)

    # create a list of tasks for the researcher
    researcher_task_context = [date_task]

    # Add retriever task if needed
    retriever_task = None
    if crewai_retriever_tool:
        retriever_task = build_retriever_task(
            researcher, query_str, crewai_retriever_tool
        )
        researcher_task_context.append(retriever_task)

    # Add search task if needed
    search_task = None
    if search_tool:
        search_task = build_search_task(
            researcher, query_str, date_tool, search_tool, crew_events_queue
        )
        researcher_task_context.append(search_task)

    chat_history = [message.content for message in chat_messages]

    research_task = Task(
        name="ResearcherTask",
        description="Research the user's question using the tools available "
        "and chat history. Based on the research return comprehensive research insights. "
        f"Given below, is the user's question and the chat history: \n<Question>:\n{query_str}\n\n<Chat history>:\n {chat_history}",
        agent=researcher,
        expected_output="A detailed analysis of the user's question based on the provided context, including relevant links and citations.",
        tools=research_tools,
        context=researcher_task_context,
        callback=lambda _: crew_events_queue.put(
            CrewEvent(type=poison_pill, name="researcher")
        ),
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
        # verbose=True,
    )
    response_task = Task(
        name="ResponderTask",
        description="Formulate a comprehensive response based on the research findings and calculations, including any relevant links and citations.",
        agent=responder,
        expected_output="A accurate response to the user's question.",
        context=[research_task],
    )

    # Create a crew with the agents and tasks
    agents = []
    tasks = []

    for task in researcher_task_context:
        tasks.append(task)
    agents.extend([researcher, responder])
    tasks.extend([research_task, calculation_task, response_task])

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
) -> str:

    # Run the crew to get the enhanced response
    crew_result: CrewOutput = crew.kickoff()

    # Create an enhanced query that includes the CrewAI insights
    return f"""
        Original query: {query_str}

        Research insights: {crew_result}

        Please provide a response to the original query, incorporating the insights from research.
        If insights from the research are used, provide in-line citations to the research findings.
        The citations should provide a link to the research findings.
        """


def stream_chat(
    use_retrieval: bool,
    llm: LLM,
    chat_engine: Optional[FlexibleContextChatEngine],
    enhanced_query: str,
    chat_messages: list[ChatMessage],
) -> StreamingAgentChatResponse:
    # Use the existing chat engine with the enhanced query for streaming response
    chat_response: StreamingAgentChatResponse
    if use_retrieval and chat_engine:
        chat_response = chat_engine.stream_chat(enhanced_query, chat_messages)
    else:
        # If the planner decides to answer directly, bypass retrieval
        logger.debug("Planner decided to answer directly without retrieval")
        logger.debug("querying llm directly with enhanced query: \n%s", enhanced_query)

        # Use the chat engine to answer directly without retrieval context
        chat_response = StreamingAgentChatResponse(
            chat_stream=llm.stream_chat(
                messages=chat_messages
                + [ChatMessage(role="user", content=enhanced_query)],
            ),
            sources=[],
            source_nodes=[],
            is_writing_to_memory=False,
        )

    return chat_response
