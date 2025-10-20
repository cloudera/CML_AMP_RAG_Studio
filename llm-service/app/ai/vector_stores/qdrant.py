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
from typing import Optional, cast

import qdrant_client
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.vector_stores.qdrant import (
    QdrantVectorStore as LlamaIndexQdrantVectorStore,
)
from qdrant_client.http.models import CountResult, Record

from .vector_store import VectorStore
from ...config import settings
from ...services import models
from ...services.metadata_apis import data_sources_metadata_api

logger = logging.getLogger(__name__)


def _new_qdrant_client() -> qdrant_client.QdrantClient:
    auth_token: str | None = settings.cdsw_apiv2_key

    def auth_token_provider() -> str:
        return auth_token or "You should never see this"

    logger.info(
        "Using Qdrant host: %s, port: %s, grpc port: %s",
        settings.qdrant_host,
        settings.qdrant_port,
        settings.qdrant_grpc_port,
    )
    
    return qdrant_client.QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        auth_token_provider=auth_token_provider if auth_token else None,
        timeout=settings.qdrant_timeout,
        prefer_grpc=True,
        grpc_port=settings.qdrant_grpc_port,
    )


class QdrantVectorStore(VectorStore):
    @staticmethod
    def for_chunks(
        data_source_id: int, client: Optional[qdrant_client.QdrantClient] = None
    ) -> "QdrantVectorStore":
        return QdrantVectorStore(
            table_name=f"index_{data_source_id}",
            data_source_id=data_source_id,
            client=client,
        )

    @staticmethod
    def for_summaries(
        data_source_id: int, client: Optional[qdrant_client.QdrantClient] = None
    ) -> "QdrantVectorStore":
        return QdrantVectorStore(
            table_name=f"summary_index_{data_source_id}",
            data_source_id=data_source_id,
            client=client,
        )

    def __init__(
        self,
        table_name: str,
        data_source_id: int,
        client: Optional[qdrant_client.QdrantClient] = None,
    ):
        self.client = client or _new_qdrant_client()
        self.table_name = table_name
        self.data_source_id = data_source_id

    def get_embedding_model(self) -> BaseEmbedding:
        data_source_metadata = data_sources_metadata_api.get_metadata(
            self.data_source_id
        )
        return models.Embedding.get(data_source_metadata.embedding_model)

    def size(self) -> Optional[int]:
        """If the collection does not exist, return None."""
        if not self.exists():
            return None
        document_count: CountResult = self.client.count(self.table_name)
        return document_count.count

    def delete(self) -> None:
        if self.exists():
            self.client.delete_collection(self.table_name)

    def delete_document(self, document_id: str) -> None:
        if self.exists():
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.llama_vector_store(),
                embed_model=models.Embedding.get_noop(),
            )
            index.delete_ref_doc(document_id)

    def exists(self) -> bool:
        return self.client.collection_exists(self.table_name)

    def llama_vector_store(self) -> BasePydanticVectorStore:
        vector_store = LlamaIndexQdrantVectorStore(
            collection_name=self.table_name,
            client=self.client,
            parallel=4,
            batch_size=64,
            max_retries=3,
        )
        return vector_store

    def visualize(
        self, user_query: Optional[str] = None
    ) -> list[tuple[tuple[float, float], str]]:
        if not self.exists():
            return []
        records: list[Record]
        records, _ = self.client.scroll(self.table_name, limit=5000, with_vectors=True)

        embeddings: list[list[float]] = []
        filenames: list[str] = []
        record: Record
        for record in records:
            payload = record.payload
            if payload:
                filename = payload.get("file_name")
                if filename:
                    filenames.append(filename)
                    embeddings.append(cast(list[float], record.vector))

        return self.visualize_embeddings(embeddings, filenames, user_query)
