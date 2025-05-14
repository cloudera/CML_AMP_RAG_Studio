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
from queue import Queue
from typing import Optional

from crewai import Task, Process, Crew, Agent, CrewOutput
from crewai_tools import SerperDevTool
from llama_index.core import QueryBundle, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from llama_index.core.llms import LLM

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.services.query.agents.date_tool import DateTool
from app.services.query.agents.models import get_crewai_llm_object_direct
from app.services.query.agents.planner_agent import PlannerAgent
from app.services.query.chat_engine import (
    build_flexible_chat_engine,
    FlexibleContextChatEngine,
)
from app.services.query.flexible_retriever import FlexibleRetriever
from app.services.query.query_configuration import QueryConfiguration

logger = logging.getLogger(__name__)

# logging.getLogger("asyncio").setLevel(logging.DEBUG)


def output_task_progress(obj: any) -> None:
    print("progress obj:", obj)
    # await asyncio.get_event_loop().create_task(asyncio.sleep(0.1))


def stream_crew_ai(
    llm: LLM,
    embedding_model: Optional[BaseEmbedding],
    chat_messages: list[ChatMessage],
    index: Optional[VectorStoreIndex],
    query_str: str,
    configuration: QueryConfiguration,
    data_source_id: int,
    crew_events_queue: Queue,
) -> tuple[StreamingAgentChatResponse, str | None]:
    crew_events_queue.put("I BELIEVE IN FERRIES ⛴️")

    use_retrieval = should_use_retrieval(
        configuration, data_source_id, llm, query_str, chat_messages
    )

    condensed_question: str = ""
    chat_response: StreamingAgentChatResponse

    crewai_llm = get_crewai_llm_object_direct(llm, configuration.model_name)
    crew_events_queue.put("building crew tasks")
    # Define tasks for the agents
    date_finder, date_task, date_tool = build_date_agent(crewai_llm)
    search_task, searcher, serper = build_search_agent(crewai_llm, date_tool)
    calculation_task, calculator = build_calculator_agent(crewai_llm)

    chat_engine: Optional[FlexibleContextChatEngine] = None
    context: str = ""
    chat_history = [message.content for message in chat_messages]
    if use_retrieval:
        crew_events_queue.put("using retrieval engine")
        chat_engine = build_flexible_chat_engine(
            configuration, llm, embedding_model, index, data_source_id
        )
        logger.info("querying chat engine")

        condensed_question = chat_engine.condense_question(
            chat_messages, query_str
        ).strip()
        # If the planner decides to use retrieval, proceed with the current flow
        logger.info("Planner decided to use retrieval")

        # First, get the context from the retriever
        query_bundle = QueryBundle(query_str=query_str)
        base_retriever = FlexibleRetriever(
            configuration=configuration,
            index=index,
            embedding_model=embedding_model,
            data_source_id=data_source_id,
            llm=llm,
        )
        retrieved_nodes = base_retriever.retrieve(query_bundle)
        context += "\n\n".join([node.node.get_content() for node in retrieved_nodes])

    researcher = Agent(
        role="Researcher",
        goal="Find the most accurate and relevant information",
        backstory="You are an expert researcher who provides accurate and relevant information based on the provided context.",
        llm=crewai_llm,
        # verbose=True,
        tools=[date_tool, serper],
        # callbacks=[pause],
    )
    research_task = Task(
        name="ResearcherTask",
        description=f"Research the following query using any provided context and chat history: {query_str}\n\nContext: {context} \n\nChat history: {chat_history}",
        agent=researcher,
        expected_output="A detailed analysis of the query based on the provided context",
        tools=[date_tool, serper],
        context=[search_task, date_task],
        callback=lambda _: crew_events_queue.put("Done"),
    )

    # Create a responder agent that formulates the final response
    responder = Agent(
        role="Responder",
        goal="Provide a comprehensive and accurate response to the query",
        backstory="You are an expert at formulating clear, concise, and accurate responses based on research findings.",
        llm=crewai_llm,
        # callbacks=[pause],
        # verbose=True,
    )
    response_task = Task(
        name="ResponderTask",
        description="Formulate a comprehensive response based on the research findings and calculations",
        agent=responder,
        expected_output="A comprehensive and accurate response to the query",
        context=[search_task, date_task, research_task, calculation_task],
        # callback=pause,
    )

    # Create a crew with the agents and tasks
    crew = Crew(
        agents=[date_finder, searcher, researcher, calculator, responder],
        tasks=[date_task, search_task, research_task, calculation_task, response_task],
        process=Process.sequential,
        name="QueryCrew",
        task_callback=output_task_progress,
    )
    crew_events_queue.put("running the crew")
    # yield from send_event_to_queue

    # Run the crew to get the enhanced response
    crew_result: CrewOutput = crew.kickoff()
    # logger.info(f"CrewAI result: {crew_result}")

    # Create an enhanced query that includes the CrewAI insights
    enhanced_query = f"""
        Original query: {query_str}

        Research insights: {crew_result}

        Please provide a comprehensive response to the original query, incorporating the insights from research.
        """

    # Use the existing chat engine with the enhanced query for streaming response
    if use_retrieval:
        chat_response = chat_engine.stream_chat(enhanced_query, chat_messages)
    else:
        # If the planner decides to answer directly, bypass retrieval
        logger.info("Planner decided to answer directly without retrieval")
        logger.info("querying llm directly with enhanced query: \n%s", enhanced_query)

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

    return chat_response, condensed_question


def build_calculator_agent(crewai_llm_name):
    calculator = Agent(
        role="Calculator",
        goal="Perform accurate mathematical calculations based on research findings",
        backstory="You are an expert mathematician who can perform complex calculations and data analysis.",
        llm=crewai_llm_name,
        verbose=True,
        # callbacks=[pause],
    )
    calculation_task = Task(
        name="CalculatorTask",
        description="Perform any necessary calculations based on the research findings. If the query requires numerical analysis, perform the calculations and show your work. If no calculations are needed, simply state that no calculations are required.",
        agent=calculator,
        expected_output="Results of any calculations performed, with step-by-step workings",
        # callback=lambda x: send_event_to_queue.send("date_tool"),
    )
    return calculation_task, calculator


def build_search_agent(crewai_llm_name, date_tool):
    serper = SerperDevTool()
    searcher = Agent(
        role="Search Agent",
        goal="Search the internet for relevant information",
        backstory="You know everything about the web.  You can find anything that exists on the web.",
        llm=crewai_llm_name,
        tools=[date_tool, serper],
        verbose=True,
        # callbacks=[pause],
    )
    search_task = Task(
        name="SearchTask",
        description="Search the internet for relevant information related to the query.",
        agent=searcher,
        tools=[date_tool],
        expected_output="Results of any search performed, with step-by-step workings",
        # callback=lambda x: send_event_to_queue.send("date_tool"),
    )
    return search_task, searcher, serper


def build_date_agent(crewai_llm):
    date_finder = Agent(
        role="DateFinder",
        goal="Find the current date and time",
        backstory="You are an expert at finding the current date and time.",
        llm=crewai_llm,
        verbose=True,
        # callbacks=[pause],
    )
    date_tool = DateTool()
    date_task = Task(
        name="DateFinderTask",
        description="Find the current date and time.",
        agent=date_finder,
        expected_output="The current date and time.",
        tools=[date_tool],
        # async_execution=True,
        # callback=lambda x: send_event_to_queue.send("date_tool"),
    )
    return date_finder, date_task, date_tool


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
    use_retrieval = planning_decision.get("use_retrieval", True)
    return use_retrieval
