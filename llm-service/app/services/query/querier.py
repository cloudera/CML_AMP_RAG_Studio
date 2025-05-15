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

from queue import Queue
from typing import Optional, TYPE_CHECKING

from llama_index.core.base.embeddings.base import BaseEmbedding

from .agents.crewai_querier import (
    assemble_crew,
    should_use_retrieval,
    launch_crew,
    stream_chat,
    CrewEvent,
    poison_pill,
)

if TYPE_CHECKING:
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
from .chat_engine import build_flexible_chat_engine, FlexibleContextChatEngine
from ...ai.vector_stores.vector_store_factory import VectorStoreFactory

logger = logging.getLogger(__name__)


def streaming_query(
    chat_engine: Optional[FlexibleContextChatEngine],
    data_source_id: Optional[int],
    query_str: str,
    configuration: QueryConfiguration,
    chat_messages: list[ChatMessage],
    crew_events_queue: Queue[CrewEvent],
) -> StreamingAgentChatResponse:
    embedding_model, index = build_datasource_query_components(data_source_id)

    llm = models.LLM.get(model_name=configuration.model_name)

    chat_response: StreamingAgentChatResponse
    if configuration.use_tool_calling:
        use_retrieval = should_use_retrieval(
            configuration,
            data_source_id,
            llm,
            query_str,
            chat_messages,
        )
        crew = assemble_crew(
            use_retrieval,
            llm,
            embedding_model,
            chat_messages,
            index,
            query_str,
            configuration,
            data_source_id,
            crew_events_queue,
        )
        enhanced_query = launch_crew(
            crew,
            query_str,
        )
        chat_response = stream_chat(
            use_retrieval,
            llm,
            chat_engine,
            enhanced_query,
            chat_messages,
        )
        return chat_response
    if not chat_engine:
        raise HTTPException(
            status_code=500,
            detail="Chat engine is not initialized. Please check the configuration.",
        )

    try:
        chat_response = chat_engine.stream_chat(query_str, chat_messages)
        crew_events_queue.put(CrewEvent(type=poison_pill, name="no-op"))
        logger.debug("query response received from chat engine")
    except botocore.exceptions.ClientError as error:
        logger.warning(error.response)
        json_error = error.response
        raise HTTPException(
            status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
            detail=json_error["message"],
        ) from error

    return chat_response

def build_datasource_query_components(
    data_source_id: Optional[int],
) -> tuple[Optional[BaseEmbedding], Optional[VectorStoreIndex]]:
    if data_source_id is None:
        return None, None
    qdrant_store = VectorStoreFactory.for_chunks(data_source_id)
    vector_store = qdrant_store.llama_vector_store()
    embedding_model = qdrant_store.get_embedding_model()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )
    return embedding_model, index


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
    llm = models.LLM.get(model_name=configuration.model_name)

    chat_engine = build_flexible_chat_engine(
        configuration, llm, embedding_model, index, data_source_id
    )

    chat_messages = list(
        map(
            lambda message: ChatMessage(role=message.role, content=message.content),
            chat_history,
        )
    )

    condensed_question: str = chat_engine.condense_question(
        chat_messages, query_str
    ).strip()

    try:
        chat_response: AgentChatResponse = chat_engine.chat(query_str, chat_messages)
        logger.debug("query response received from chat engine")
        return chat_response, condensed_question
    except botocore.exceptions.ClientError as error:
        logger.warning(error.response)
        json_error = error.response
        raise HTTPException(
            status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
            detail=json_error["message"],
        ) from error
