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

from llama_index.core.agent import ReActAgent
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata, BaseTool, FunctionTool

from .tools import multiply

if typing.TYPE_CHECKING:
    from ..chat import RagContext

import logging
from typing import List, Optional

import botocore.exceptions
from fastapi import HTTPException
from llama_index.core import PromptTemplate, QueryBundle
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.llms import LLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore

from app.services import models
from app.services.query.query_configuration import QueryConfiguration
from .chat_engine import FlexibleContextChatEngine
from .flexible_retriever import FlexibleRetriever
from .simple_reranker import SimpleReranker
from ..metadata_apis.data_sources_metadata_api import get_metadata
from ...ai.vector_stores.vector_store_factory import VectorStoreFactory

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
) -> tuple[AgentChatResponse, str | None]:
    llm = models.LLM.get(model_name=configuration.model_name)

    tools = []

    # Create a chat message list from the chat history
    chat_messages = list(
        map(
            lambda message: ChatMessage(role=message.role, content=message.content),
            chat_history,
        )
    )

    def format_and_call_llm(content: str):
        messages = chat_messages.copy()
        user_message = ChatMessage(role="user", content=content)
        messages.append(user_message)
        return llm.chat(messages).message.content

    # Create a direct_llm_chat tool
    direct_llm_chat_tool = FunctionTool.from_defaults(
        fn=format_and_call_llm,
        name="direct_llm_chat_tool",
        description="Directly chat with the LLM. Used as a fallback when no other suitable tools are available.",
    )

    tools.append(direct_llm_chat_tool)
    condensed_question = None

    # Create a retriever tool
    if data_source_id != -1:
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
        chat_engine = _build_flexible_chat_engine(
            configuration, llm, retriever, data_source_id
        )

        logger.info("querying chat engine")

        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=chat_engine._get_response_synthesizer(
                chat_history=chat_messages
            ),
        )

        # todo: add summary as description
        query_engine_tool = QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name="Knowledge_base_retriever",
                description="Retrieves documents from the knowledge base. A summary of the knowledge base's contents is below:"
                "A model for predicting COVID-19 cases has been developed by a collaboration of experts, using data on mobility to estimate future cases. It's been tested in the US and is being used in several countries to inform response strategies. Meanwhile, a document containing membership details is stored as an image, revealing information about a Peloton membership, including its status and purchase date. The membership is active and was purchased in November 2022, with a residence zip code of 80026.",
            ),
        )
        tools.append(query_engine_tool)

        # Condense the question
        condensed_question: str = chat_engine.condense_question(
            chat_messages, query_str
        ).strip()

    multiplier_tool = FunctionTool.from_defaults(
        multiply,
        name="multiplier",
        description="multiplies two integers",
    )
    tools.append(multiplier_tool)

    memory = ChatMemoryBuffer.from_defaults(token_limit=40000)

    agent = ReActAgent(tools=tools, llm=llm, verbose=True, memory=memory)

    try:
        # chat_response: AgentChatResponse = chat_engine.chat(query_str, chat_messages)
        chat_response: AgentChatResponse = agent.chat(
            message=query_str, chat_history=chat_messages
        )
        # chat_response: AgentChatResponse = chat_engine.chat(query_str, chat_messages)
        logger.info("query response received from chat engine")
        return chat_response, condensed_question
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
    return FlexibleRetriever(configuration, index, embedding_model, data_source_id, llm)


class DebugNodePostProcessor(BaseNodePostprocessor):
    def _postprocess_nodes(
        self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle] = None
    ) -> list[NodeWithScore]:
        logger.info(f"nodes: {len(nodes)}")
        for node in sorted(nodes, key=lambda n: n.node.node_id):
            logger.info(
                node.node.node_id, node.node.metadata["document_id"], node.score
            )

        return nodes


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
        configuration, data_source_id=data_source_id, llm=llm
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
