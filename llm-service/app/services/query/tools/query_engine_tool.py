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
from __future__ import annotations

import logging
from typing import List, Optional

from llama_index.core import VectorStoreIndex, QueryBundle, PromptTemplate
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.schema import NodeWithScore
from llama_index.core.tools import QueryEngineTool, ToolMetadata

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.ai.vector_stores.vector_store_factory import VectorStoreFactory
from app.services import models
from app.services.metadata_apis.data_sources_metadata_api import get_metadata
from app.services.query.chat_engine import FlexibleContextChatEngine
from app.services.query.flexible_retriever import FlexibleRetriever
from app.services.query.query_configuration import QueryConfiguration
from app.services.query.simple_reranker import SimpleReranker

logger = logging.getLogger(__name__)


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


def _create_retriever(
    configuration: QueryConfiguration,
    embedding_model: BaseEmbedding,
    index: VectorStoreIndex,
    data_source_id: int,
    llm: LLM,
) -> BaseRetriever:
    return FlexibleRetriever(configuration, index, embedding_model, data_source_id, llm)


def query_engine_tool(
    chat_messages: list[ChatMessage],
    configuration: QueryConfiguration,
    data_source_id: int,
    llm: LLM,
) -> tuple[QueryEngineTool, FlexibleContextChatEngine]:
    qdrant_store = VectorStoreFactory.for_chunks(data_source_id)
    summary_indexer = SummaryIndexer.get_summary_indexer(data_source_id)
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
    summary = summary_indexer.get_full_summary()
    tool_description = "Retrieves documents from the knowledge base. Try using this tool first before any others."
    if summary is not None:
              tool_description += "\nA summary of the contents of this knowledge base is provided below:\n" + summary
    return (
        QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name="Knowledge_base_retriever",
                description=tool_description,
            ),
        ),
        chat_engine,
    )


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
