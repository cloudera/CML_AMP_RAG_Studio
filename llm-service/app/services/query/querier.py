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
import os
from typing import List, cast, Optional

import botocore.exceptions
from fastapi import HTTPException
from llama_index.core import QueryBundle, PromptTemplate
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.indices.vector_store import VectorIndexRetriever
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.schema import NodeWithScore
from pydantic import Field

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.ai.vector_stores.qdrant import QdrantVectorStore
from app.services import models
from app.services.chat_store import RagContext
from app.services.query.chat_engine import FlexibleChatEngine
from app.services.query.query_configuration import QueryConfiguration

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

    query_engine = _create_query_engine(configuration, data_source_id, embedding_model, index, llm)
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


class FlexibleRetriever(BaseRetriever):
    def __init__(self, configuration: QueryConfiguration, index: VectorStoreIndex, embedding_model: BaseEmbedding, data_source_id: int, llm: LLM) -> None:
        super().__init__()
        self.index = index
        self.configuration = configuration
        self.embedding_model = embedding_model
        self.data_source_id = data_source_id
        self.llm = llm

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        enable_doc_id_filtering = os.environ.get('ENABLE_TWO_STAGE_RETRIEVAL') or None
        # add a filter to the retriever with the resulting document ids.
        doc_ids: list[str] | None = None
        if enable_doc_id_filtering:
            doc_ids = self._filter_doc_ids_by_summary(query_bundle.query_str)

        base_retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=self.configuration.top_k,
            embed_model=self.embedding_model,  # is this needed, really, if it's in the index?
            doc_ids=doc_ids or None,
        )
        res: List[NodeWithScore] = base_retriever.retrieve(query_bundle)
        return res

    def _filter_doc_ids_by_summary(self, query_str: str) -> list[str] | None:
        try:
            # first query the summary index to get documents to filter by (assuming summarization is enabled)
            summary_engine = SummaryIndexer(data_source_id=self.data_source_id, splitter=SentenceSplitter(chunk_size=2048),
                                            embedding_model=self.embedding_model, llm=self.llm, ).as_query_engine()
            summaries: list[NodeWithScore] = summary_engine.retrieve(QueryBundle(query_str))

            def document_ids(node: NodeWithScore) -> str:
                return cast(str, node.metadata["document_id"])

            doc_ids: list[str] = list(map(document_ids, summaries))
            return doc_ids
        except Exception as e:
            logger.debug(f"Failed to retrieve document ids from summary index: {e}")
            return None

def _create_retriever(configuration: QueryConfiguration, embedding_model: BaseEmbedding,
                      index: VectorStoreIndex, data_source_id: int, llm: LLM) -> BaseRetriever:
    return FlexibleRetriever(configuration, index, embedding_model, data_source_id, llm)

class SimpleReranker(BaseNodePostprocessor):
    top_n: int = Field(description="The number of nodes to return", gt=0)
    def __init__(self, top_n: int = 5):
        super().__init__(top_n=top_n)

    def _postprocess_nodes(self,
                            nodes: List[NodeWithScore],
                            query_bundle: Optional[QueryBundle] = None) -> List[NodeWithScore]:
        nodes.sort(key=lambda x: x.score, reverse=True)
        return nodes[:self.top_n]


def _create_query_engine(configuration: QueryConfiguration, data_source_id: int, embedding_model: BaseEmbedding, index: VectorStoreIndex, llm: LLM) -> RetrieverQueryEngine:
    retriever = _create_retriever(configuration, embedding_model, index, data_source_id, llm)
    response_synthesizer = get_response_synthesizer(llm=llm)
    query_engine = RetrieverQueryEngine(
        retriever=retriever, response_synthesizer=response_synthesizer, node_postprocessors=[SimpleReranker(top_n=configuration.top_k)]
    )
    return query_engine

def _build_chat_engine(configuration: QueryConfiguration, llm: LLM,
                       query_engine: RetrieverQueryEngine) -> FlexibleChatEngine:
    chat_engine: FlexibleChatEngine = FlexibleChatEngine.from_defaults(
        query_engine=query_engine,
        llm=llm,
        condense_question_prompt=CUSTOM_PROMPT,
    )
    chat_engine.configuration = configuration
    return chat_engine
