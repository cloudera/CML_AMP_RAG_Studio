import time
start_time = time.time()
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
import logging
from typing import cast

from llama_index.core import QueryBundle, VectorStoreIndex
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.indices.vector_store import VectorIndexRetriever
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import NodeWithScore

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.services.metadata_apis.data_sources_metadata_api import get_metadata
from app.services.query.query_configuration import QueryConfiguration

logger = logging.getLogger(__name__)


class FlexibleRetriever(BaseRetriever):
    def __init__(
        self,
        configuration: QueryConfiguration,
        index: VectorStoreIndex,
        embedding_model: BaseEmbedding,
        data_source_id: int,
        llm: LLM,
    ) -> None:
        super().__init__()
        self.index = index
        self.configuration = configuration
        self.embedding_model = embedding_model
        self.data_source_id = data_source_id
        self.llm = llm

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        summarization_model = get_metadata(self.data_source_id).summarization_model

        base_retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=self.configuration.top_k,
            embed_model=self.embedding_model,  # is this needed, really, if it's in the index?
        )

        result_nodes: list[NodeWithScore] = base_retriever.retrieve(query_bundle)
        logger.debug(f"result_nodes: {len(result_nodes)}")

        for node in sorted(result_nodes, key=lambda n: n.node.node_id):
            logger.debug(
                node.node.node_id, node.node.metadata["document_id"], node.score
            )

        if summarization_model is not None and self.configuration.use_summary_filter:
            # add a filter to the retriever with the resulting document ids.
            doc_ids = self._filter_doc_ids_by_summary(query_bundle.query_str)
            if doc_ids:
                simple_retriever = VectorIndexRetriever(
                    index=self.index,
                    similarity_top_k=self.configuration.top_k,
                    embed_model=self.embedding_model,  # is this needed, really, if it's in the index?
                    doc_ids=doc_ids,
                )
                result_nodes.extend(simple_retriever.retrieve(query_bundle))
        logger.debug(f"result_nodes(2): {len(result_nodes)}")
        for node in sorted(result_nodes, key=lambda n: n.node.node_id):
            logger.debug(
                node.node.node_id, node.node.metadata["document_id"], node.score
            )
        return result_nodes

    def _filter_doc_ids_by_summary(self, query_str: str) -> list[str] | None:
        try:
            # first query the summary index to get documents to filter by (assuming summarization is enabled)
            summary_engine = SummaryIndexer(
                data_source_id=self.data_source_id,
                splitter=SentenceSplitter(chunk_size=2048),
                embedding_model=self.embedding_model,
                llm=self.llm,
            ).as_query_engine()
            summaries: list[NodeWithScore] = summary_engine.retrieve(
                QueryBundle(query_str)
            )

            def document_ids(node: NodeWithScore) -> str:
                return cast(str, node.metadata["document_id"])

            doc_ids: list[str] = list(map(document_ids, summaries))
            return doc_ids
        except Exception as e:
            logger.debug(f"Failed to retrieve document ids from summary index: {e}")
            return None

print(f'services/query/flexible_retriever.py took {time.time() - start_time} seconds to import')
