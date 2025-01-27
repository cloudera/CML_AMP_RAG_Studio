#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
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
import logging

import botocore.exceptions
from fastapi import HTTPException
from llama_index.core import PromptTemplate
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.llms import LLM
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer

from app.ai.vector_stores.qdrant import QdrantVectorStore
from app.services import models
from app.services.chat_store import RagContext
from app.services.query.chat_engine import FlexibleChatEngine
from app.services.query.query_configuration import QueryConfiguration
from .flexible_retriever import FlexibleRetriever
from ..metadata_apis.data_sources_metadata_api import get_metadata

logger = logging.getLogger(__name__)

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


def query(
    data_source_id: int,
    query_str: str,
    configuration: QueryConfiguration,
    chat_history: list[RagContext],
) -> AgentChatResponse:
    qdrant_store = QdrantVectorStore.for_chunks(data_source_id)
    vector_store = qdrant_store.llama_vector_store()
    embedding_model = qdrant_store.get_embedding_model()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )
    logger.info("fetched Qdrant index")
    llm = models.get_llm(model_name=configuration.model_name)

    query_engine = _create_query_engine(
        configuration, data_source_id, embedding_model, index, llm
    )
    chat_engine = _build_chat_engine(configuration, llm, query_engine)

    logger.info("querying chat engine")
    chat_messages = list(
        map(
            lambda message: ChatMessage(role=message.role, content=message.content),
            chat_history,
        )
    )

    try:
        chat_response: AgentChatResponse = chat_engine.chat(query_str, chat_messages)
        logger.info("query response received from chat engine")
        return chat_response
    except botocore.exceptions.ClientError as error:
        logger.warning(error.response)
        json_error = error.response
        raise HTTPException(
            status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
            detail=json_error["message"],
        ) from error


def _create_retriever(
    configuration: QueryConfiguration,
    embedding_model: BaseEmbedding,
    index: VectorStoreIndex,
    data_source_id: int,
    llm: LLM,
) -> BaseRetriever:
    print("configuration:", configuration)
    return FlexibleRetriever(configuration, index, embedding_model, data_source_id, llm)


def _create_query_engine(
    configuration: QueryConfiguration,
    data_source_id: int,
    embedding_model: BaseEmbedding,
    index: VectorStoreIndex,
    llm: LLM,
) -> RetrieverQueryEngine:
    retriever = _create_retriever(
        configuration, embedding_model, index, data_source_id, llm
    )
    response_synthesizer = get_response_synthesizer(llm=llm)

    summarization_model = get_metadata(
        data_source_id=data_source_id,
    ).summarization_model
    reranker = models.get_reranking_model(
        summarization_enabled=bool(summarization_model is not None),
        model_name=configuration.rerank_model_name,
        top_n=configuration.top_k,
    )
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[reranker],
    )
    return query_engine


def _build_chat_engine(
    configuration: QueryConfiguration, llm: LLM, query_engine: RetrieverQueryEngine
) -> FlexibleChatEngine:
    chat_engine: FlexibleChatEngine = FlexibleChatEngine.from_defaults(
        query_engine=query_engine,
        llm=llm,
        condense_question_prompt=CUSTOM_PROMPT,
    )
    chat_engine.configuration = configuration
    return chat_engine
