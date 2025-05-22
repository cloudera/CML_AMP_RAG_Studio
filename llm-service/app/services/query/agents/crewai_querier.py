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
import re
import time
from queue import Queue
from typing import Optional, Any, Tuple

import opik
from crewai import Task, Process, Crew, Agent, CrewOutput, TaskOutput
from crewai.agents.parser import AgentFinish
from crewai.tools.base_tool import BaseTool
from crewai_tools import SerperDevTool
from crewai_tools.tools.llamaindex_tool.llamaindex_tool import LlamaIndexTool
from llama_index.core import QueryBundle, VectorStoreIndex
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from llama_index.core.llms import LLM
from llama_index.core.schema import NodeWithScore
from llama_index.core.tools import RetrieverTool, ToolMetadata, ToolOutput
from pydantic import BaseModel, Field

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


def step_callback(output: Any, agent: str, crew_events_queue: Queue[CrewEvent]) -> None:
    if isinstance(output, AgentFinish):
        crew_events_queue.put(
            CrewEvent(
                type="agent_finish",
                name=agent,
                data=output.thought,
                timestamp=time.time(),
            )
        )
    if isinstance(output, TaskOutput):
        crew_events_queue.put(
            CrewEvent(
                type="task_completed",
                name=agent,
                data=output.raw,
                timestamp=time.time(),
            )
        )


def build_calculation_task(
    agent: Agent,
    calculation_task_context: list[Task],
    crew_events_queue: Queue[CrewEvent],
) -> Task:
    """
    Build a calculation task for the agent.
    This task will perform any necessary calculations based on the research findings.

    Args:
        agent (Agent): The agent that will perform the calculations.
        calculation_task_context (list[Task]): The list of Task objects that will be used as context for the calculation task.
        crew_events_queue (Queue[CrewEvent]): The queue to send events to.

    Returns:
        Task: The calculation task.
    """
    calculation_task = Task(
        name="CalculatorTask",
        description="Perform any necessary calculations based on the research findings. If the query requires numerical analysis, perform the calculations and show your work. If no calculations are needed, simply state that no calculations are required.",
        agent=agent,
        context=calculation_task_context if calculation_task_context else None,
        expected_output="Results of any calculations performed, with step-by-step workings",
        callback=lambda output: step_callback(
            output, "Calculation Complete", crew_events_queue
        ),
    )
    return calculation_task


class SearchResult(BaseModel):
    result: str | None = None
    link: str | None = None


class SearchOutput(BaseModel):
    search_results: list[SearchResult]


def build_search_task(
    agent: Agent,
    query: str,
    chat_history: str,
    search_task_context: list[Task],
    search_tool: SerperDevTool,
    crew_events_queue: Queue[CrewEvent],
) -> Task:
    """
    Build a search task for the agent.
    This task will search the internet for relevant information related to the user's question and chat history.

    Args:
        agent (Agent): The agent that will perform the search.
        query (str): The user's question.
        chat_history (list[str | None]): The chat history.
        search_task_context (list[Task]): The list of Task objects that will be used as context for the search task.
        search_tool (SerperDevTool): The search tool to be used.
        crew_events_queue (Queue[CrewEvent]): The queue to send events to.

    Returns:
        Task: The search task.
    """
    search_task = Task(
        name="SearchTask",
        description="Search the internet for relevant information related to the user's question and chat history.\n\n"
        f"<Chat history>:\n{chat_history}\n\n<Question>:\n{query}\n\n"
        "If the question can be answered using the chat history or the context, do not use the search tool and "
        "return blank strings for the search results. If needed, use the chat history to refine the user's "
        "question to pass as input to the search tool.",
        agent=agent,
        tools=[search_tool],
        context=search_task_context if search_task_context else None,
        expected_output="Results of any search performed, with step-by-step workings, including links to the sources.",
        output_json=SearchOutput,
        callback=lambda output: step_callback(
            output, "Search Complete", crew_events_queue
        ),
    )
    return search_task


class RetrieverToolInput(BaseModel):
    """Input Schema for the RetrieverTool."""

    query: str = Field(
        ...,
        description="The query to search for in the index.",
    )


class RetrieverToolWithNodeInfo(RetrieverTool):
    """
    Retriever tool.

    A tool making use of a retriever.

    Args:
        retriever (BaseRetriever): A retriever.
        metadata (ToolMetadata): The associated metadata of the query engine.
        node_postprocessors (Optional[List[BaseNodePostprocessor]]): A list of
            node postprocessors.
    """

    def call(self, *args: Any, **kwargs: Any) -> ToolOutput:
        query_str = ""
        if args is not None:
            query_str += ", ".join([str(arg) for arg in args]) + "\n"
        if kwargs is not None:
            query_str += (
                ", ".join([f"{k!s} is {v!s}" for k, v in kwargs.items()]) + "\n"
            )
        if query_str == "":
            raise ValueError("Cannot call query engine without inputs")

        docs = self._retriever.retrieve(query_str)
        docs = self._apply_node_postprocessors(docs, QueryBundle(query_str))
        content = ""
        for doc in docs:
            node_copy = doc.node.model_copy()
            node_copy.text_template = "{metadata_str}\n{content}"
            node_copy.metadata_template = "{key} = {value}"
            content += (
                f"node_id = {node_copy.node_id}\n"
                + f"score = {doc.score}\n"
                + node_copy.get_content()
                + "\n\n"
            )
        return ToolOutput(
            content=content,
            tool_name=self.metadata.name if self.metadata.name else "RetrieverTool",
            raw_input={"input": query_str},
            raw_output=docs,
        )

    async def acall(self, *args: Any, **kwargs: Any) -> ToolOutput:
        query_str = ""
        if args is not None:
            query_str += ", ".join([str(arg) for arg in args]) + "\n"
        if kwargs is not None:
            query_str += (
                ", ".join([f"{k!s} is {v!s}" for k, v in kwargs.items()]) + "\n"
            )
        if query_str == "":
            raise ValueError("Cannot call query engine without inputs")
        docs = await self._retriever.aretrieve(query_str)
        content = ""
        docs = self._apply_node_postprocessors(docs, QueryBundle(query_str))
        for doc in docs:
            node_copy = doc.node.model_copy()
            node_copy.text_template = "{metadata_str}\n{content}"
            node_copy.metadata_template = "{key} = {value}"
            content += (
                f"node_id = {node_copy.node_id}\n"
                + f"score = {doc.score}\n"
                + node_copy.get_content()
                + "\n\n"
            )
        return ToolOutput(
            content=content,
            tool_name=self.metadata.name if self.metadata.name else "RetrieverTool",
            raw_input={"input": query_str},
            raw_output=docs,
        )


def build_retriever_tool(
    configuration: QueryConfiguration,
    data_source_id: int,
    embedding_model: BaseEmbedding,
    index: VectorStoreIndex,
    llm: LLM,
) -> BaseTool:
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
    retriever_tool = RetrieverToolWithNodeInfo(
        retriever=base_retriever,
        metadata=ToolMetadata(
            name="Retriever",
            description=(
                "A tool to retrieve relevant information from "
                "the index. It takes a query of type string and returns relevant nodes from the index."
                f"The index summary is: {data_source_summary}"
                if data_source_summary
                else "Assume the index has relevant information about the user's question."
            ),
            fn_schema=RetrieverToolInput,
        ),
    )
    crewai_retriever_tool = LlamaIndexTool.from_tool(retriever_tool)
    return crewai_retriever_tool


class RetrieverResult(BaseModel):
    node_id: str | None = None
    score: float | None = None
    content: str | None = None


class RetrieverOutput(BaseModel):
    retriever_results: list[RetrieverResult]


def build_retriever_task(
    agent: Agent,
    query: str,
    chat_history: str,
    retriever_task_context: list[Task],
    retriever_tool: BaseTool,
    crew_events_queue: Queue[CrewEvent],
) -> Task:
    retriever_task = Task(
        name="RetrieverTask",
        description="Retrieve relevant information from the index based on the user's question.\n\n"
        f"<Chat history>:\n{chat_history}\n\n<Question>:\n{query}\n\n"
        "If the question can be answered using the chat history or the context, do not use the retriever tool and "
        "return blank strings for the retriever results. If needed, use the chat history to refine the user's question "
        "to pass as input to the retriever tool.",
        agent=agent,
        tools=[retriever_tool],
        context=retriever_task_context if retriever_task_context else None,
        expected_output="Relevant information retrieved from the index.",
        output_json=RetrieverOutput,
        callback=lambda output: step_callback(
            output, "Retrieval Complete", crew_events_queue
        ),
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
        callback=lambda output: step_callback(output, "Date Found", crew_events_queue),
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

    # Create a retriever tool if needed
    crewai_retriever_tool = None
    if use_retrieval and index and embedding_model and data_source_id:
        logger.info("Planner decided to use retrieval")
        crewai_retriever_tool = build_retriever_tool(
            configuration,
            data_source_id,
            embedding_model,
            index,
            llm,
        )
        research_tools.append(crewai_retriever_tool)

    # Create a search tool if needed
    search_tool = None
    if configuration.tools and "search" in configuration.tools:
        search_tool = SerperDevTool()
        research_tools.append(search_tool)

    # Define the researcher agent
    researcher = Agent(
        role="Researcher",
        goal=f"Research and find relevant information about `{query_str}` and provide comprehensive research insights.",
        backstory="You are an expert researcher who provides accurate and relevant information. "
        "You know when to use tools and when to answer directly.",
        llm=crewai_llm,
        verbose=True,
    )

    # Define tasks for the researcher agents
    date_task = build_date_task(researcher, date_tool, crew_events_queue)

    chat_history = ""
    for message in chat_messages:
        if message.role == MessageRole.USER:
            chat_history += f"User:\n{message.content}\n"
        elif message.role == MessageRole.ASSISTANT:
            chat_history += f"Assistant:\n{message.content}\n"

    # create a list of tasks for the researcher
    researcher_task_context = [date_task]

    # Add retriever task if needed
    retriever_task = None
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

    # Add search task if needed
    search_task = None
    if search_tool:
        search_task_context = [date_task]
        if retriever_task:
            search_task_context.append(retriever_task)
        search_task = build_search_task(
            researcher,
            query_str,
            chat_history,
            search_task_context,
            search_tool,
            crew_events_queue,
        )
        researcher_task_context.append(search_task)

    research_task = Task(
        name="ResearcherTask",
        description="Research the user's question using the context available "
        "and chat history. Based on the research return comprehensive research insights. "
        "Given below, is the user's question and the chat history: \n\n"
        f"<Chat history>:\n{chat_history}\n\n<Question>:\n{query_str}",
        agent=researcher,
        expected_output="A detailed analysis of the user's question based on the provided context, "
        "including relevant links and in-line citations."
        "Note: \n"
        "* Use the citations from the chat history as is. "
        "* Use links and result from the search results (search_results) if needed to answer the question "
        "and cite them in the given format: the link should be in markdown format. For example: "
        "[link](https://example.com). Do not make up links that are not present chat history or context.\n"
        "* Cite from retriever results (retriever_results) in the given format: the node_id "
        "should be in an html anchor tag (<a href>) with an html 'class' of 'rag_citation'. "
        "Do not use filenames as citations. Only node ids should be used."
        "For example: <a class='rag_citation' href='2'>2</a>. Do not make up node ids that are not present "
        "in the context.\n"
        "* All citations should be either in-line citations or markdown links. ",
        context=researcher_task_context,
        callback=lambda output: step_callback(
            output, "Research Complete", crew_events_queue
        ),
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
        # verbose=True,
    )
    response_task = Task(
        name="ResponderTask",
        description="Formulate a comprehensive response based on the research findings and calculations, "
        "including any relevant links and in-line citations.",
        agent=responder,
        expected_output="A accurate response to the user's question. The links and citations are to be copied as is "
        "from the context. Do not format it, or change it in any way.",
        context=[research_task, calculation_task],
        callback=lambda _: crew_events_queue.put(
            CrewEvent(type=poison_pill, name="responder")
        ),
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
) -> Tuple[str, list[Tuple[str, float]]]:
    # Run the crew to get the enhanced response
    crew_result: CrewOutput = crew.kickoff()

    source_node_ids_w_score = extract_node_ids_from_crew_result(crew_result)

    # Create an enhanced query that includes the CrewAI insights
    return (
        f"""
Original query: {query_str}

Research insights: {crew_result}

Please provide a response to the original query, incorporating the insights from research with in-line citations. \
If insights from the research are used, use the links and in-line citations from the research insights as is. \
Keep markdown formatted links as is. Keep the in-line citations of format `<a class='rag_citation' \
href='node_id'>node_id</a>` as is.
""",
        source_node_ids_w_score,
    )


def extract_node_ids_from_crew_result(
    crew_result: CrewOutput,
) -> list[Tuple[str, float]]:
    # find if RetrieverTask in tasks_outputs
    source_node_ids_w_score = []
    # Extract the retriever results from the crew result
    for task_output in crew_result.tasks_output:
        if task_output.name == "RetrieverTask":
            if task_output.json_dict:
                json_output = task_output.json_dict["retriever_results"]
                for result in json_output:
                    node_id = result["node_id"]
                    score = result["score"]
                    if node_id and score:
                        # Append the node id and score to the list
                        source_node_ids_w_score.append((node_id, score))
    # Extract the node ids from the crew result string
    crew_result_str = crew_result.raw
    extracted_node_ids = re.findall(
        r"<a class='rag_citation' href='(.*?)'>",
        crew_result_str,
    )
    # add the extracted node ids to the source node ids
    source_node_ids = set([node_id for node_id, _ in source_node_ids_w_score])
    for node_id in extracted_node_ids:
        if node_id not in source_node_ids:
            source_node_ids_w_score.append((node_id, 0.0))
    return source_node_ids_w_score


def stream_chat(
    use_retrieval: bool,
    llm: LLM,
    chat_engine: Optional[FlexibleContextChatEngine],
    enhanced_query: str,
    source_nodes: list[NodeWithScore],
    chat_messages: list[ChatMessage],
) -> StreamingAgentChatResponse:
    # Use the existing chat engine with the enhanced query for streaming response
    chat_response: StreamingAgentChatResponse
    if use_retrieval and chat_engine:
        chat_response = StreamingAgentChatResponse(
            chat_stream=llm.stream_chat(
                messages=chat_messages
                + [ChatMessage(role="user", content=enhanced_query)],
            ),
            source_nodes=source_nodes,
            is_writing_to_memory=False,
        )
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
