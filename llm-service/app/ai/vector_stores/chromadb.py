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
from abc import ABC
from typing import Optional, List, cast, Any, Mapping

import fastapi.exceptions
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import BaseNode
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.vector_stores.chroma import (
    ChromaVectorStore as LlamaIndexChromaVectorStore,
)
from llama_index.core.indices import VectorStoreIndex
import chromadb
from chromadb.api import ClientAPI
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection

from app.ai.vector_stores.vector_store import VectorStore
from app.config import settings
from app.services.metadata_apis import data_sources_metadata_api
from app.services.models import Embedding

logger = logging.getLogger(__name__)


def _new_chroma_client() -> ClientAPI:
    # Note: chromadb.HttpClient requires host and port; ssl, token, database, and tenant are optional depending on server setup
    # We default to HTTP client to support external ChromaDB servers.
    try:
        client_kwargs: dict[str, Any] = {
            "host": settings.chromadb_host,
            "headers": (
                {"X-Chroma-Token": f"{settings.chromadb_token}"}
                if settings.chromadb_token
                else None
            ),
        }

        if settings.chromadb_database:
            client_kwargs["database"] = settings.chromadb_database
        if settings.chromadb_tenant:
            client_kwargs["tenant"] = settings.chromadb_tenant

        # Always pass Settings to control telemetry; add SSL verify when provided
        settings_kwargs: dict[str, Any] = {
            "anonymized_telemetry": settings.chromadb_enable_anonymized_telemetry,
        }
        if settings.chromadb_server_ssl_cert_path:
            settings_kwargs["chroma_server_ssl_verify"] = (
                settings.chromadb_server_ssl_cert_path
            )
        client_kwargs["settings"] = Settings(**settings_kwargs)

        # Only pass port if explicitly provided. If host includes https, Chroma infers SSL.
        if settings.chromadb_port is not None:
            client_kwargs["port"] = settings.chromadb_port

        client: ClientAPI = chromadb.HttpClient(**client_kwargs)
        return client
    except Exception:
        logger.error("Failed to create ChromaDB client", exc_info=True)
        raise


class ChromaVectorStore(VectorStore, ABC):
    """ChromaDB Vector Store."""

    @staticmethod
    def for_chunks(data_source_id: int) -> "ChromaVectorStore":
        return ChromaVectorStore(
            data_source_id=data_source_id,
            collection_name=f"{settings.chromadb_tenant}__{settings.chromadb_database}__index_{data_source_id}",
        )

    @staticmethod
    def for_summaries(data_source_id: int) -> "ChromaVectorStore":
        return ChromaVectorStore(
            data_source_id=data_source_id,
            collection_name=f"{settings.chromadb_tenant}__{settings.chromadb_database}__summary_index_{data_source_id}",
        )

    def __init__(
        self,
        data_source_id: int,
        collection_name: str,
        client: Optional[ClientAPI] = None,
    ):
        self._client = client or _new_chroma_client()
        self.collection_name = collection_name
        self.data_source_id = data_source_id

    def get_embedding_model(self) -> BaseEmbedding:
        datasource_metadata = data_sources_metadata_api.get_metadata(
            self.data_source_id
        )
        return Embedding.get(datasource_metadata.embedding_model)

    def size(self) -> Optional[int]:
        if not self.exists():
            return None
        try:
            collection = self._client.get_collection(self.collection_name)
            # Chroma does not provide a direct count without fetching; use count() if available
            try:
                # newer chromadb exposes count()
                return collection.count()
            except Exception:
                # Return None if we cannot determine efficiently
                return None
        except Exception:
            logger.exception(
                "Error getting size for collection %s",
                self.collection_name,
            )
            return None

    def delete(self) -> None:
        if not self.exists():
            return None
        try:
            self._client.delete_collection(self.collection_name)
        except Exception as exc:
            logger.exception("Failed to delete collection %s", self.collection_name)
            raise fastapi.exceptions.HTTPException(
                500, "Failed to delete collection"
            ) from exc

    def delete_document(self, document_id: str) -> None:
        if not self.exists():
            return None
        try:
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.llama_vector_store(),
                embed_model=Embedding.get_noop(),
            )
            index.delete_ref_doc(document_id)
        except Exception as exc:
            logger.error(
                "Failed to delete document %s from %s",
                document_id,
                self.collection_name,
            )
            raise fastapi.exceptions.HTTPException(
                500, "Failed to delete document"
            ) from exc

    def exists(self) -> bool:
        try:
            self._client.get_collection(self.collection_name)
            return True
        except Exception:
            return False

    def llama_vector_store(self) -> BasePydanticVectorStore:
        chroma_collection: Collection = self._client.get_or_create_collection(
            self.collection_name
        )
        return LlamaIndexChromaVectorStore(
            chroma_collection=chroma_collection,
        )

    def visualize(
        self, user_query: Optional[str] = None
    ) -> list[tuple[tuple[float, float], str]]:
        if not self.exists():
            return []
        try:
            collection = self._client.get_collection(self.collection_name)
            # fetch some items to visualize; include embeddings and file names
            # chroma get can include embeddings and metadatas
            results = collection.get(include=["embeddings", "metadatas"], limit=5000)
            embeddings: List[List[float]] = []
            filenames: List[str] = []
            if isinstance(results, dict):
                raw_embeddings = results.get("embeddings")
                raw_metadatas = results.get("metadatas")
                if isinstance(raw_embeddings, list):
                    for idx, embedding in enumerate(raw_embeddings):
                        metadata_entry: Mapping[str, Any] | None = None
                        if isinstance(raw_metadatas, list) and idx < len(raw_metadatas):
                            possible = raw_metadatas[idx]
                            if isinstance(possible, dict):
                                metadata_entry = possible
                        filename_value = (
                            metadata_entry.get("file_name") if metadata_entry else None
                        )
                        if isinstance(filename_value, str) and isinstance(
                            embedding, list
                        ):
                            filenames.append(filename_value)
                            embeddings.append(cast(List[float], embedding))

            return self.visualize_embeddings(embeddings, filenames, user_query)
        except Exception:
            logger.error(
                "Visualization failed for collection %s",
                self.collection_name,
                exc_info=True,
            )
            return []

    def get_chunk_contents(self, chunk_id: str) -> BaseNode:
        # For parity with base VectorStore convenience method, use llama_index vector_store get_nodes
        return self.llama_vector_store().get_nodes([chunk_id])[0]
