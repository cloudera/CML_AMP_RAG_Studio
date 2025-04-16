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
import functools
import os
from abc import ABC
from typing import Optional

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from app.ai.vector_stores.vector_store import VectorStore
from llama_index.vector_stores.opensearch import (
    OpensearchVectorStore,
    OpensearchVectorClient,
)

from app.services.metadata_apis import data_sources_metadata_api
from app.services.models import Embedding
from opensearchpy.client import OpenSearch as OpensearchClient


def _new_opensearch_client(dim: int, index: str) -> OpensearchVectorClient:

    return OpensearchVectorClient(
        # username=os.environ.get("OPENSEARCH_USERNAME", "admin"),
        # password=os.environ.get("OPENSEARCH_INITIAL_ADMIN_PASSWORD"),
        endpoint=os.environ.get("OPENSEARCH_ENDPOINT", "http://localhost:9200"),
        index=index,
        dim=dim,
    )


class OpenSearch(VectorStore, ABC):
    """OpenSearch Vector Store."""

    @staticmethod
    def for_chunks(data_source_id: int) -> "OpenSearch":
        return OpenSearch(
            data_source_id=data_source_id,
            table_name=f"index_{data_source_id}",
        )

    @staticmethod
    def for_summaries(data_source_id: int) -> "OpenSearch":
        return OpenSearch(
            data_source_id=data_source_id,
            table_name=f"summary_index_{data_source_id}",
        )

    def __init__(
        self,
        table_name: str,
        data_source_id: int,
    ):
        self.table_name = table_name
        self.data_source_id = data_source_id

    @staticmethod
    @functools.cache
    def _find_dim(data_source_id: int) -> int:
        datasource_metadata = data_sources_metadata_api.get_metadata(data_source_id)
        embedding_model = Embedding.get(datasource_metadata.embedding_model)
        vector = embedding_model.get_query_embedding("any")
        return len(vector)

    def size(self) -> Optional[int]:
        os_client = OpensearchClient(
            os.environ.get("OPENSEARCH_ENDPOINT", "http://localhost:9200")
        )
        count = os_client.count(index=self.table_name)
        print(f"{count=}")
        return count["count"]

    def delete(self) -> None:
        os_client = OpensearchClient(
            os.environ.get("OPENSEARCH_ENDPOINT", "http://localhost:9200")
        )
        os_client.indices.delete(index=self.table_name)

    def delete_document(self, document_id: str) -> None:
        self._get_client().delete_by_doc_id(document_id)

    def llama_vector_store(self) -> BasePydanticVectorStore:
        return OpensearchVectorStore(
            self._get_client(),
        )

    def _get_client(self):
        return _new_opensearch_client(
            dim=self._find_dim(self.data_source_id),
            index=self.table_name,
        )

    def exists(self) -> bool:
        os_client = OpensearchClient(
            os.environ.get("OPENSEARCH_ENDPOINT", "http://localhost:9200")
        )
        exists = os_client.indices.exists(index=self.table_name)
        print(f"{exists=}")
        return exists

    def visualize(
        self, user_query: Optional[str] = None
    ) -> list[tuple[tuple[float, float], str]]:
        # todo: implement this
        pass

    def get_embedding_model(self) -> BaseEmbedding:
        datasource_metadata = data_sources_metadata_api.get_metadata(
            self.data_source_id
        )
        return Embedding.get(datasource_metadata.embedding_model)
