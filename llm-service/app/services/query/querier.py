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
# ##############################################################################
from __future__ import annotations

import typing
import logging

from llama_index.core import VectorStoreIndex, PromptTemplate
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor

from app.services.query.tools.react_agent import configure_react_agent
from .chat_engine import FlexibleContextChatEngine
from .flexible_retriever import FlexibleRetriever
from .simple_reranker import SimpleReranker
from .tools.query_engine_tool import DebugNodePostProcessor
from .. import models
from ..metadata_apis.data_sources_metadata_api import get_metadata
from ...ai.vector_stores.vector_store_factory import VectorStoreFactory

if typing.TYPE_CHECKING:
    from ..chat import RagContext


import botocore.exceptions
from fastapi import HTTPException
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import AgentChatResponse

from app.services.query.query_configuration import QueryConfiguration

logger = logging.getLogger(__name__)


def query(
    data_source_id: int | None,
    query_str: str,
    configuration: QueryConfiguration,
    chat_history: list[RagContext],
) -> tuple[AgentChatResponse, str | None]:

    # Create a chat message list from the chat history
    chat_messages = list(
        map(
            lambda message: ChatMessage(role=message.role, content=message.content),
            chat_history,
        )
    )

    total_data_sources_size: int = 0
    if data_source_id:
        total_data_sources_size = VectorStoreFactory.for_chunks(data_source_id).size()

    chat_engine: FlexibleContextChatEngine | None = None
    condensed_question: str | None = None
    if (
        data_source_id is not None
        and not configuration.exclude_knowledge_base
        and total_data_sources_size > 0
    ):
        chat_engine = create_chat_engine(configuration, data_source_id)
        condensed_question = chat_engine.condense_question(
            chat_messages, query_str
        ).strip()

    if configuration.use_tool_calling:
        chatter = configure_react_agent(
            chat_messages, configuration, chat_engine, data_source_id
        ).chat
    elif chat_engine is not None:
        chatter = chat_engine.chat
    else:

        def direct_llm_completion(
            message: str,
            chat_history: list[ChatMessage],
        ) -> AgentChatResponse:
            chat_history.append(ChatMessage.from_str(message, role="user"))
            bare_chat_response = models.LLM.get(
                model_name=configuration.model_name
            ).chat(messages=chat_history)
            return AgentChatResponse(
                response=bare_chat_response.message.content or "",
            )

        chatter = direct_llm_completion

    try:
        chat_response: AgentChatResponse = chatter(
            message=query_str, chat_history=chat_messages
        )
        logger.info("query response received from chat engine")
        return chat_response, condensed_question
    except botocore.exceptions.ClientError as error:
        logger.warning(error.response)
        json_error = error.response
        raise HTTPException(
            status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
            detail=json_error["message"],
        ) from error


def create_chat_engine(
    configuration: QueryConfiguration,
    data_source_id: int,
) -> FlexibleContextChatEngine:
    llm = models.LLM.get(model_name=configuration.model_name)
    qdrant_store = VectorStoreFactory.for_chunks(data_source_id)
    vector_store = qdrant_store.llama_vector_store()
    embedding_model = qdrant_store.get_embedding_model()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )
    logger.info("fetched Qdrant index")
    retriever = _create_retriever(
        configuration, embedding_model, index, data_source_id, llm
    )
    return _build_flexible_chat_engine(configuration, llm, retriever, data_source_id)


def _create_node_postprocessors(
    configuration: QueryConfiguration, data_source_id: int, llm: LLM
) -> list[BaseNodePostprocessor]:
    if not configuration.use_postprocessor:
        return []

    data_source = get_metadata(data_source_id=data_source_id)
    if data_source.summarization_model is None:
        return [SimpleReranker(top_n=configuration.top_k)]

    return [
        DebugNodePostProcessor(),
        models.Reranking.get(
            model_name=configuration.rerank_model_name,
            top_n=configuration.top_k,
        )
        or SimpleReranker(top_n=configuration.top_k),
        DebugNodePostProcessor(),
    ]


def _build_flexible_chat_engine(
    configuration: QueryConfiguration,
    llm: LLM,
    retriever: BaseRetriever,
    data_source_id: int,
) -> FlexibleContextChatEngine:
    postprocessors = _create_node_postprocessors(
        configuration,
        data_source_id=data_source_id,
        llm=llm,
    )
    chat_engine: FlexibleContextChatEngine = FlexibleContextChatEngine.from_defaults(
        llm=llm,
        condense_question_prompt=CUSTOM_PROMPT,
        retriever=retriever,
        node_postprocessors=postprocessors,
        chat_mode="react",
    )
    chat_engine._configuration = configuration
    return chat_engine


def _create_retriever(
    configuration: QueryConfiguration,
    embedding_model: BaseEmbedding,
    index: VectorStoreIndex,
    data_source_id: int,
    llm: LLM,
) -> BaseRetriever:
    return FlexibleRetriever(configuration, index, embedding_model, data_source_id, llm)


CUSTOM_TEMPLATE = """\
Given a conversation (between Human and Assistant) and a follow up message from Human, \
rewrite the message to be a standalone question that captures all relevant context \
from the conversation. Just provide the question, not any description of it.

<Chat History>
{chat_history}

<Follow Up Message>
{question}

<Standalone question>
"""
CUSTOM_PROMPT = PromptTemplate(CUSTOM_TEMPLATE)
