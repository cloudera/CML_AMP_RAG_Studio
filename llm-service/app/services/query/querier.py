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

import re
from typing import Optional, TYPE_CHECKING, cast

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.schema import NodeWithScore
from llama_index.llms.bedrock_converse.utils import (
    BEDROCK_FUNCTION_CALLING_MODELS,
    get_model_name,
)
from llama_index.llms.openai.utils import (
    is_function_calling_model,
    ALL_AVAILABLE_MODELS,
)

from .agents.tool_calling_querier import (
    should_use_retrieval,
    stream_chat,
)
from .flexible_retriever import FlexibleRetriever
from .multi_retriever import MultiSourceRetriever
from ..metadata_apis.session_metadata_api import Session
from ..models.providers import (
    BedrockModelProvider,
    OpenAiModelProvider,
    AzureModelProvider,
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

LLAMA_3_2_NON_FUNCTION_CALLING_MODELS = {
    "meta.llama3-2-1b-instruct-v1:0",
    "meta.llama3-2-3b-instruct-v1:0",
}

MODIFIED_BEDROCK_FUNCTION_CALLING_MODELS = tuple(
    set(BEDROCK_FUNCTION_CALLING_MODELS) - LLAMA_3_2_NON_FUNCTION_CALLING_MODELS
)


def streaming_query(
    chat_engine: Optional[FlexibleContextChatEngine],
    query_str: str,
    configuration: QueryConfiguration,
    chat_messages: list[ChatMessage],
    session: Session,
) -> StreamingAgentChatResponse:
    llm = models.LLM.get(model_name=configuration.model_name)

    chat_response: StreamingAgentChatResponse
    if configuration.use_tool_calling:
        check_for_tool_calling_support(llm)

        use_retrieval, data_source_summaries = should_use_retrieval(
            session.get_all_data_source_ids(), configuration.exclude_knowledge_base
        )

        chat_response = stream_chat(
            use_retrieval,
            cast(FunctionCallingLLM, llm),
            chat_engine,
            query_str,
            chat_messages,
            session,
            data_source_summaries,
        )
        return chat_response
    if not chat_engine:
        raise HTTPException(
            status_code=500,
            detail="Chat engine is not initialized. Please check the configuration.",
        )

    try:
        chat_response = chat_engine.stream_chat(query_str, chat_messages)
        logger.debug("query response received from chat engine")
    except botocore.exceptions.ClientError as error:
        logger.warning(error.response)
        json_error = error.response
        detail = json_error["Error"].get("Message", None)
        raise HTTPException(
            status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
            detail=detail if detail else json_error["StatusReason"],
        ) from error

    return chat_response


# LlamaIndex's list of function-calling models appears out of date,
# so we have a modified version
def is_bedrock_function_calling_model_v2(model_name: str) -> bool:
    return get_model_name(model_name) in MODIFIED_BEDROCK_FUNCTION_CALLING_MODELS


def check_for_tool_calling_support(llm: LLM) -> None:
    if BedrockModelProvider.is_enabled() and not is_bedrock_function_calling_model_v2(
        llm.metadata.model_name
    ):
        raise HTTPException(
            status_code=422,
            detail=f"Tool calling is enabled, but the model {get_model_name(llm.metadata.model_name)} does not support tool calling.  "
            f"The following models support tool calling: {', '.join(list(MODIFIED_BEDROCK_FUNCTION_CALLING_MODELS))}.",
        )
    if (
        OpenAiModelProvider.is_enabled() or AzureModelProvider.is_enabled()
    ) and not llm.metadata.is_function_calling_model:
        openai_function_calling_models = [
            model_name
            for model_name in ALL_AVAILABLE_MODELS.keys()
            if is_function_calling_model(model_name)
        ]
        raise HTTPException(
            status_code=422,
            detail=f"Tool calling is enabled, but the model {llm.metadata.model_name} does not support tool calling. "
            f"The following models support tool calling: {', '.join(list(openai_function_calling_models))}.",
        )


def get_nodes_from_output(
    output: str,
    session: Session,
) -> list[NodeWithScore]:
    source_node_ids_w_score: dict[str, float] = {}

    # Extract the node ids from string output
    extracted_node_ids = re.findall(
        r"<a class=\"rag_citation\" href=\"(.*?)\">",
        output,
    )

    # add the extracted node ids to the source node ids
    for node_id in extracted_node_ids:
        if node_id not in source_node_ids_w_score:
            source_node_ids_w_score[node_id] = 0.0

    extracted_data_source_ids = session.get_all_data_source_ids()
    source_nodes: list[NodeWithScore] = []
    if len(source_node_ids_w_score) > 0:
        try:
            for ds_id in extracted_data_source_ids:
                node_ids = list(source_node_ids_w_score.keys())
                qdrant_store = VectorStoreFactory.for_chunks(ds_id)
                if not qdrant_store or not qdrant_store.size():
                    continue
                vector_store = qdrant_store.llama_vector_store()
                extracted_source_nodes = vector_store.get_nodes(node_ids=node_ids)

                # cast them into NodeWithScore with score 0.0
                source_nodes.extend(
                    [
                        NodeWithScore(
                            node=node,
                            score=source_node_ids_w_score.get(node.node_id, 0.0),
                        )
                        for node in extracted_source_nodes
                    ]
                )
        except Exception as e:
            logger.warning(
                "Failed to extract nodes from response citations (%s): %s",
                extracted_node_ids,
                e,
            )
            pass
    return source_nodes


def build_datasource_query_components(
    data_source_id: int,
) -> tuple[BaseEmbedding, VectorStoreIndex]:
    qdrant_store = VectorStoreFactory.for_chunks(data_source_id)
    vector_store = qdrant_store.llama_vector_store()
    embedding_model = qdrant_store.get_embedding_model()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )
    return embedding_model, index


def query(
    session: Session,
    query_str: str,
    configuration: QueryConfiguration,
    chat_history: list[RagContext],
    should_condense_question: bool = True,
) -> tuple[AgentChatResponse, str | None]:
    llm = models.LLM.get(model_name=configuration.model_name)
    retriever = build_retriever(configuration, session.get_all_data_source_ids(), llm)

    chat_engine = build_flexible_chat_engine(configuration, llm, retriever)

    if not chat_engine:
        raise HTTPException(
            status_code=500,
            detail="Chat engine is not initialized. Please check the configuration.",
        )

    chat_messages = list(
        map(
            lambda message: ChatMessage(role=message.role, content=message.content),
            chat_history,
        )
    )

    condensed_question: str | None = None
    if should_condense_question:
        condensed_question = chat_engine.condense_question(
            chat_messages, query_str
        ).strip()

    try:
        chat_response: AgentChatResponse = chat_engine.chat(query_str, chat_messages)
        logger.debug("query response received from chat engine")
        return chat_response, condensed_question
    except botocore.exceptions.ClientError as error:
        logger.warning(error.response)
        json_error = error.response
        detail = json_error["Error"].get("Message", None)
        raise HTTPException(
            status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
            detail=detail if detail else json_error["StatusReason"],
        ) from error


def build_retriever(
    configuration: QueryConfiguration,
    data_source_ids: list[int],
    llm: LLM,
) -> Optional[BaseRetriever]:
    retrievers: list[FlexibleRetriever] = []
    for data_source_id in data_source_ids:
        if data_source_id is None:
            continue

        chunks = VectorStoreFactory.for_chunks(data_source_id)
        if not chunks or not chunks.size():
            continue

        embedding_model, vector_store = build_datasource_query_components(
            data_source_id
        )
        retriever = FlexibleRetriever(
            configuration, vector_store, embedding_model, data_source_id, llm
        )
        retrievers.append(retriever)
    return MultiSourceRetriever(retrievers)
