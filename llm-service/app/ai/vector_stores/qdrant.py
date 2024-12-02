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

import os
from typing import Optional, Any
import umap

import qdrant_client
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.vector_stores.qdrant import (
    QdrantVectorStore as LlamaIndexQdrantVectorStore,
)
from qdrant_client.http.models import CountResult, Record

from .vector_store import VectorStore
from ...services import models


def new_qdrant_client() -> qdrant_client.QdrantClient:
    host = os.environ.get("QDRANT_HOST", "localhost")
    port = 6333
    return qdrant_client.QdrantClient(host=host, port=port)


class QdrantVectorStore(VectorStore):
    @staticmethod
    def for_chunks(
            data_source_id: int, client: Optional[qdrant_client.QdrantClient] = None
    ) -> "QdrantVectorStore":
        return QdrantVectorStore(table_name=f"index_{data_source_id}", client=client)

    @staticmethod
    def for_summaries(
            data_source_id: int, client: Optional[qdrant_client.QdrantClient] = None
    ) -> "QdrantVectorStore":
        return QdrantVectorStore(
            table_name=f"summary_index_{data_source_id}", client=client
        )

    def __init__(
            self, table_name: str, client: Optional[qdrant_client.QdrantClient] = None
    ):
        self.client = client or new_qdrant_client()
        self.table_name = table_name

    def size(self) -> Optional[int]:
        """
        If the collection does not exist, return -1
        """
        if not self.client.collection_exists(self.table_name):
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
                embed_model=models.get_embedding_model(),
            )
            index.delete_ref_doc(document_id)

    def exists(self) -> bool:
        return self.client.collection_exists(self.table_name)

    def llama_vector_store(self) -> BasePydanticVectorStore:
        vector_store = LlamaIndexQdrantVectorStore(self.table_name, self.client)
        return vector_store

    def visualize(self, user_query: Optional[str] = None) -> list[tuple[tuple[float, float], str]]:
        records: list[Record]
        records, _ = self.client.scroll(self.table_name, limit=5000, with_vectors=True)

        if user_query:
            embedding_model = models.get_embedding_model()
            user_query_vector = embedding_model.get_query_embedding(user_query)
            records.append(Record(vector=user_query_vector, id="abc123", payload={"file_name": "USER_QUERY"}))

        record: Record
        filenames = []
        for record in records:
            payload: dict[str, Any] | None = record.payload
            if payload:
                filenames.append(payload.get("file_name"))

        reducer = umap.UMAP()
        embeddings = [record.vector for record in records]
        reduced_embeddings = reducer.fit_transform(embeddings)

        # todo: figure out how to satisfy mypy on this line
        return [(tuple(coordinate), filenames[i]) for i, coordinate in enumerate(reduced_embeddings.tolist())] # type: ignore
