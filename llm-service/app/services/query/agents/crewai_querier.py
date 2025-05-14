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
from typing import Optional

from llama_index.core import QueryBundle, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from llama_index.core.llms import LLM

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.services.query.agents.planner_agent import PlannerAgent
from app.services.query.agents.query_crew import query_crew
from app.services.query.chat_engine import (
    build_flexible_chat_engine,
    FlexibleContextChatEngine,
)
from app.services.query.flexible_retriever import FlexibleRetriever
from app.services.query.query_configuration import QueryConfiguration

logger = logging.getLogger(__name__)

logging.getLogger("asyncio").setLevel(logging.DEBUG)

def pause(obj: any) -> None:
    print("pausing with obj:", obj)
    # await asyncio.get_event_loop().create_task(asyncio.sleep(0.1))


async def stream_crew_ai(
    llm: LLM,
    embedding_model: Optional[BaseEmbedding],
    chat_messages: list[ChatMessage],
    index: Optional[VectorStoreIndex],
    query_str: str,
    configuration: QueryConfiguration,
    data_source_id: int,
) -> tuple[StreamingAgentChatResponse, str]:
    use_retrieval = should_use_retrieval(
        configuration, data_source_id, llm, query_str, chat_messages
    )

    condensed_question: str = ""
    chat_response: StreamingAgentChatResponse

    chat_engine: Optional[FlexibleContextChatEngine] = None
    context: str = ""
    chat_history = [message.content for message in chat_messages]
    if use_retrieval:
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

    crew = query_crew(llm, configuration, query_str, context, chat_history)

    # Run the crew to get the enhanced response
    crew_result = crew.kickoff()
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
