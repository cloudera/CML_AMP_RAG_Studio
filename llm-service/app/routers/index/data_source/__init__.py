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
import tempfile
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv
from llama_index.core.node_parser import SentenceSplitter
from pydantic import BaseModel

from .... import exceptions
from ....ai.indexing.embedding_indexer import EmbeddingIndexer
from ....ai.indexing.summary_indexer import SummaryIndexer
from ....ai.vector_stores.qdrant import QdrantVectorStore
from ....ai.vector_stores.vector_store import VectorStore
from ....services import data_sources_metadata_api, doc_summaries, models, s3

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data_sources/{data_source_id}", tags=["Data Sources"])


class SummarizeDocumentRequest(BaseModel):
    document_id: str
    s3_bucket_name: str
    s3_document_key: str
    original_filename: str


class RagIndexDocumentConfiguration(BaseModel):
    # TODO: Add more params
    chunk_size: int = 512  # this is llama-index's default
    chunk_overlap: int = 10  # percentage of tokens in a chunk (chunk_size)


class RagIndexDocumentRequest(BaseModel):
    document_id: str
    s3_bucket_name: str
    s3_document_key: str
    original_filename: str
    configuration: RagIndexDocumentConfiguration = RagIndexDocumentConfiguration()


class ChunkContentsResponse(BaseModel):
    text: str
    metadata: Dict[str, Any]


@cbv(router)
class DataSourceController:
    chunks_vector_store: VectorStore = Depends(
        lambda data_source_id: QdrantVectorStore.for_chunks(data_source_id)
    )

    @staticmethod
    def _get_summary_indexer(data_source_id: int) -> SummaryIndexer:
        datasource = data_sources_metadata_api.get_metadata(data_source_id)
        return SummaryIndexer(
            data_source_id=data_source_id,
            splitter=SentenceSplitter(chunk_size=2048),
            llm=models.get_llm(datasource.summarization_model),
        )

    @router.get(
        "/size",
        summary="Returns the number of chunks in the data source.",
        response_model=None,
    )
    @exceptions.propagates
    def size(self) -> int:
        return self.chunks_vector_store.size() or 0

    @router.get(
        "/chunks/{chunk_id}",
        summary="Returns the content of a chunk.",
        response_model=None,
    )
    @exceptions.propagates
    def chunk_contents(self, chunk_id: str) -> ChunkContentsResponse:
        node = self.chunks_vector_store.llama_vector_store().get_nodes([chunk_id])[0]
        return ChunkContentsResponse(
            text=node.get_content(),
            metadata=node.metadata,
        )

    @router.get("/visualize")
    @exceptions.propagates
    def visualize(self) -> list[tuple[tuple[float, float], str]]:
        return self.chunks_vector_store.visualize()

    class VisualizationRequest(BaseModel):
        user_query: str

    @router.post("/visualize")
    @exceptions.propagates
    def visualize_with_query(
        self, request: VisualizationRequest
    ) -> list[tuple[tuple[float, float], str]]:
        return self.chunks_vector_store.visualize(request.user_query)

    @router.delete(
        "/", summary="Deletes the data source from the index.", response_model=None
    )
    @exceptions.propagates
    def delete(self, data_source_id: int) -> None:
        self.chunks_vector_store.delete()
        self._get_summary_indexer(data_source_id).delete_data_source()

    @router.get(
        "/documents/{doc_id}/summary",
        summary="summarize a single document",
        response_model=None,
    )
    @exceptions.propagates
    def get_document_summary(self, data_source_id: int, doc_id: str) -> str:
        indexer = self._get_summary_indexer(data_source_id)
        summary = indexer.get_summary(doc_id)
        if not summary:
            return "No summary found for this document."
        return summary

    @router.get(
        "/summary",
        summary="summarize all documents for a datasource",
        response_model=None,
    )
    @exceptions.propagates
    def get_document_summary_of_summaries(self, data_source_id: int) -> str:
        return doc_summaries.summarize_data_source(data_source_id)

    @router.post(
        "/summarize-document", summary="summarize a document", response_model=None
    )
    @exceptions.propagates
    def summarize_document(
        self,
        data_source_id: int,
        request: SummarizeDocumentRequest,
    ) -> str:
        with tempfile.TemporaryDirectory() as tmpdirname:
            logger.debug("created temporary directory %s", tmpdirname)
            file_path = s3.download(
                tmpdirname,
                request.s3_bucket_name,
                request.s3_document_key,
                request.original_filename,
            )

            indexer = self._get_summary_indexer(data_source_id)
            # Delete to avoid duplicates
            indexer.delete_document(request.document_id)
            indexer.index_file(file_path, request.document_id)
            summary = indexer.get_summary(request.document_id)
            assert summary is not None
            return summary

    @router.delete(
        "/documents/{doc_id}", summary="delete a single document", response_model=None
    )
    @exceptions.propagates
    def delete_document(self, data_source_id: int, doc_id: str) -> None:
        self.chunks_vector_store.delete_document(doc_id)
        self._get_summary_indexer(data_source_id).delete_document(doc_id)

    @router.post(
        "/documents/download-and-index",
        summary="Download and index document",
        description="Download document from S3 and index in Pinecone",
        response_model=None,
    )
    @exceptions.propagates
    def download_and_index(
        self,
        data_source_id: int,
        request: RagIndexDocumentRequest,
    ) -> None:
        datasource = data_sources_metadata_api.get_metadata(data_source_id)
        with tempfile.TemporaryDirectory() as tmpdirname:
            logger.debug("created temporary directory %s", tmpdirname)
            file_path = s3.download(
                tmpdirname,
                request.s3_bucket_name,
                request.s3_document_key,
                request.original_filename,
            )

            indexer = EmbeddingIndexer(
                data_source_id,
                splitter=SentenceSplitter(
                    chunk_size=request.configuration.chunk_size,
                    chunk_overlap=int(
                        request.configuration.chunk_overlap
                        * 0.01
                        * request.configuration.chunk_size
                    ),
                ),
                embedding_model=models.get_embedding_model(datasource.embedding_model),
                chunks_vector_store=self.chunks_vector_store,
            )
            # Delete to avoid duplicates
            self.chunks_vector_store.delete_document(request.document_id)
            indexer.index_file(file_path, request.document_id)
