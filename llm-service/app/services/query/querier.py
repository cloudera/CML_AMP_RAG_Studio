# ##############################################################################
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
#  contrary, (A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
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
# ##############################################################################
from __future__ import annotations

import typing

from .tools.crewai_querier import stream_crew_ai
from ...ai.indexing.summary_indexer import SummaryIndexer

if typing.TYPE_CHECKING:
    from ..chat.utils import RagContext

import logging

import botocore.exceptions
from fastapi import HTTPException
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import (
    AgentChatResponse,
    StreamingAgentChatResponse,
)
from llama_index.core.indices import VectorStoreIndex

from app.services import models
from app.services.query.query_configuration import QueryConfiguration
from .chat_engine import  build_flexible_chat_engine
from .planner_agent import PlannerAgent
from ...ai.vector_stores.vector_store_factory import VectorStoreFactory

logger = logging.getLogger(__name__)


def streaming_query(
    data_source_id: int,
    query_str: str,
    configuration: QueryConfiguration,
    chat_history: list[RagContext],
) -> tuple[StreamingAgentChatResponse, str | None]:
    qdrant_store = VectorStoreFactory.for_chunks(data_source_id)
    vector_store = qdrant_store.llama_vector_store()
    embedding_model = qdrant_store.get_embedding_model()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )
    llm = models.LLM.get(model_name=configuration.model_name)

    chat_messages = list(
        map(
            lambda message: ChatMessage(role=message.role, content=message.content),
            chat_history,
        )
    )
    chat_response: StreamingAgentChatResponse
    condensed_question: str
    if configuration.use_tool_calling:
        chat_response, condensed_question = stream_crew_ai(
            llm,
            embedding_model,
            chat_messages,
            index,
            query_str,
            configuration,
            data_source_id,
        )
    else:
        chat_engine = build_flexible_chat_engine(
            configuration=configuration,
            llm=llm,
            embedding_model=embedding_model,
            index=index,
            data_source_id=data_source_id,
        )

        condensed_question = chat_engine.condense_question(
            chat_messages, query_str
        ).strip()
        try:
            chat_response = chat_engine.stream_chat(
                query_str, chat_messages
            )
            logger.info("query response received from chat engine")
        except botocore.exceptions.ClientError as error:
            logger.warning(error.response)
            json_error = error.response
            raise HTTPException(
                status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
                detail=json_error["message"],
            ) from error

    return chat_response, condensed_question


def query(
    data_source_id: int,
    query_str: str,
    configuration: QueryConfiguration,
    chat_history: list[RagContext],
) -> tuple[AgentChatResponse, str | None]:
    qdrant_store = VectorStoreFactory.for_chunks(data_source_id)
    vector_store = qdrant_store.llama_vector_store()
    embedding_model = qdrant_store.get_embedding_model()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )
    logger.info("fetched Qdrant index")
    llm = models.LLM.get(model_name=configuration.model_name)

    chat_engine = build_flexible_chat_engine(
        configuration, llm, embedding_model, index, data_source_id
    )

    logger.info("querying chat engine")
    chat_messages = list(
        map(
            lambda message: ChatMessage(role=message.role, content=message.content),
            chat_history,
        )
    )

    condensed_question: str = chat_engine.condense_question(
        chat_messages, query_str
    ).strip()

    data_source_summary_indexer = SummaryIndexer.get_summary_indexer(data_source_id)
    data_source_summary = None
    if data_source_summary_indexer:
        data_source_summary = data_source_summary_indexer.get_full_summary()

    try:
        # Create a planner agent to decide whether to use retrieval or answer directly
        planner = PlannerAgent(llm, configuration)
        planning_decision = planner.decide_retrieval_strategy(
            query_str, data_source_summary
        )

        logger.info(f"Planner decision: {planning_decision}")

        chat_response: AgentChatResponse
        if planning_decision.get("use_retrieval", True):
            # If the planner decides to use retrieval, proceed with the current flow
            logger.info("Planner decided to use retrieval")
            chat_response = chat_engine.chat(query_str, chat_messages)
        else:
            # If the planner decides to answer directly, bypass retrieval
            logger.info("Planner decided to answer directly without retrieval")

            # Create a direct query with the explanation from the planner
            direct_query = f"""
            Original query: {query_str}

            The planner has determined that this query can be answered directly without retrieval.
            Explanation: {planning_decision.get('explanation', 'No explanation provided')}

            Please provide a comprehensive response to the query using your general knowledge.
            """

            # Use the chat engine to answer directly without retrieval context
            chat_response = chat_engine.chat(direct_query, chat_messages)

        logger.info("query response received from chat engine")
        return chat_response, condensed_question
    except botocore.exceptions.ClientError as error:
        logger.warning(error.response)
        json_error = error.response
        raise HTTPException(
            status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
            detail=json_error["message"],
        ) from error
