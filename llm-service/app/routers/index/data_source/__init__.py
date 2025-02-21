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
from http import HTTPStatus
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from pydantic import BaseModel

from .... import exceptions
from ....ai.indexing.base import NotSupportedFileExtensionError
from ....ai.indexing.embedding_indexer import EmbeddingIndexer
from ....ai.indexing.summary_indexer import SummaryIndexer
from ....ai.vector_stores.qdrant import QdrantVectorStore
from ....ai.vector_stores.vector_store import VectorStore
from ....services import document_storage, models
from ....services.metadata_apis import data_sources_metadata_api
from ....services.metadata_apis.data_sources_metadata_api import RagDataSource
from ....services.mlflow import write_mlflow_run_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data_sources/{data_source_id}", tags=["Data Sources"])

SUMMARIZATION_DISABLED = "Summarization disabled. Please specify a summarization model in the knowledge base to enable."


class SummarizeDocumentRequest(BaseModel):
    s3_bucket_name: str
    s3_document_key: str
    original_filename: str


class RagIndexDocumentConfiguration(BaseModel):
    chunk_size: int = 512  # this is llama-index's default
    chunk_overlap: int = 10  # percentage of tokens in a chunk (chunk_size)


class RagIndexDocumentRequest(BaseModel):
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
    def _get_summary_indexer(data_source_id: int) -> Optional[SummaryIndexer]:
        datasource = data_sources_metadata_api.get_metadata(data_source_id)
        if not datasource.summarization_model:
            return None
        return SummaryIndexer(
            data_source_id=data_source_id,
            splitter=SentenceSplitter(chunk_size=2048),
            embedding_model=models.get_embedding_model(datasource.embedding_model),
            llm=models.get_llm(datasource.summarization_model),
        )

    @router.delete(
        "/", summary="Deletes the data source from the index.", response_model=None
    )
    @exceptions.propagates
    def delete(self, data_source_id: int) -> None:
        self.chunks_vector_store.delete()
        SummaryIndexer.delete_data_source_by_id(data_source_id)

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

    @router.delete(
        "/documents/{doc_id}", summary="delete a single document", response_model=None
    )
    @exceptions.propagates
    def delete_document(self, data_source_id: int, doc_id: str) -> None:
        self.chunks_vector_store.delete_document(doc_id)
        summary_indexer = self._get_summary_indexer(data_source_id)
        if summary_indexer:
            summary_indexer.delete_document(doc_id)

    @router.post(
        "/documents/{doc_id}/index",
        summary="Download and index document",
        response_model=None,
    )
    @exceptions.propagates
    def download_and_index(
        self,
        data_source_id: int,
        doc_id: str,
        request: RagIndexDocumentRequest,
    ) -> None:
        datasource = data_sources_metadata_api.get_metadata(data_source_id)
        self._download_and_index(datasource, doc_id, request)

    def _download_and_index(
        self, datasource: RagDataSource, doc_id: str, request: RagIndexDocumentRequest
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdirname:
            logger.debug("created temporary directory %s", tmpdirname)
            doc_storage = document_storage.from_environment()
            file_path = doc_storage.download(
                tmpdirname,
                request.s3_bucket_name,
                request.s3_document_key,
                request.original_filename,
            )
            llm: Optional[LLM] = None
            if datasource.summarization_model:
                llm = models.get_llm(datasource.summarization_model)
            indexer = EmbeddingIndexer(
                datasource.id,
                splitter=SentenceSplitter(
                    chunk_size=request.configuration.chunk_size,
                    chunk_overlap=int(
                        request.configuration.chunk_overlap
                        * 0.01
                        * request.configuration.chunk_size
                    ),
                ),
                embedding_model=models.get_embedding_model(datasource.embedding_model),
                llm=llm,
                chunks_vector_store=self.chunks_vector_store,
            )
            write_mlflow_run_json(
                f"datasource_{datasource.name}_{datasource.id}",
                f"doc_{doc_id}",
                {
                    "params": {
                        "data_source_id": str(datasource.id),
                        "embedding_model": datasource.embedding_model,
                        "summarization_model": datasource.summarization_model,
                        "chunk_size": str(request.configuration.chunk_size),
                        "chunk_overlap": str(request.configuration.chunk_overlap),
                        "file_name": request.original_filename,
                        "file_size_bytes": str(file_path.stat().st_size),
                    }
                },
            )

            # Delete to avoid duplicates
            self.chunks_vector_store.delete_document(doc_id)
            try:
                indexer.index_file(file_path, doc_id)
            except NotSupportedFileExtensionError as e:
                raise HTTPException(
                    status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Unsupported file extension: {e.file_extension}",
                )

    @router.get(
        "/documents/{doc_id}/summary",
        summary="summarize a single document",
        response_model=None,
    )
    @exceptions.propagates
    def get_document_summary(self, data_source_id: int, doc_id: str) -> str:
        indexer = self._get_summary_indexer(data_source_id)
        if not indexer:
            return SUMMARIZATION_DISABLED
        summary = indexer.get_summary(doc_id)
        if not summary:
            return "No summary found for this document."
        return summary

    @router.post(
        "/documents/{doc_id}/summary",
        summary="summarize a document",
        response_model=None,
    )
    @exceptions.propagates
    def summarize_document(
        self,
        data_source_id: int,
        doc_id: str,
        request: SummarizeDocumentRequest,
    ) -> str:
        with tempfile.TemporaryDirectory() as tmpdirname:
            logger.debug("created temporary directory %s", tmpdirname)
            doc_storage = document_storage.from_environment()
            file_path = doc_storage.download(
                tmpdirname,
                request.s3_bucket_name,
                request.s3_document_key,
                request.original_filename,
            )

            indexer = self._get_summary_indexer(data_source_id)
            if not indexer:
                return SUMMARIZATION_DISABLED
            # Delete to avoid duplicates
            try:
                indexer.delete_document(doc_id)
            except Exception as e:
                # ignore, since it might just be because the summary index doesn't exist yet
                logger.info("Failed to delete document %s: %s", doc_id, e)

            try:
                indexer.index_file(file_path, doc_id)
                summary = indexer.get_summary(doc_id)
                assert summary is not None
                return summary
            except NotSupportedFileExtensionError as e:
                raise HTTPException(
                    status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Unsupported file extension: {e.file_extension}",
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
        "/summary",
        summary="summarize all documents for a datasource",
        response_model=None,
    )
    @exceptions.propagates
    def get_document_summary_of_summaries(self, data_source_id: int) -> str:
        indexer = self._get_summary_indexer(data_source_id)
        if not indexer:
            return SUMMARIZATION_DISABLED
        summary = indexer.get_full_summary()
        if not summary:
            return "No summary found for this data source."
        return summary

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
