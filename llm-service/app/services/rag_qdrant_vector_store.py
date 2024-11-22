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

import qdrant_client
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client.http.models import CountResult

from .vector_store import VectorStore


class RagQdrantVectorStore(VectorStore):
    host = os.environ.get("QDRANT_HOST", "localhost")
    port = 6333

    def __init__(self, table_name: str, memory_store: bool = False):
        self.client = self._create_qdrant_clients(memory_store)
        self.table_name = table_name

    def size(self) -> int:
        """
        If the collection does not exist, return -1
        """
        if not self.client.collection_exists(self.table_name):
            return -1
        document_count: CountResult = self.client.count(self.table_name)
        return document_count.count

    def delete(self) -> None:
        if self.exists():
            self.client.delete_collection(self.table_name)

    def exists(self) -> bool:
        return self.client.collection_exists(self.table_name)

    def _create_qdrant_clients(self, memory_store: bool) -> qdrant_client.QdrantClient:
        if memory_store:
            client = qdrant_client.QdrantClient(":memory:")
        else:
            client = qdrant_client.QdrantClient(host=self.host, port=self.port)

        return client

    def access_vector_store(self) -> BasePydanticVectorStore:
        vector_store = QdrantVectorStore(self.table_name, self.client)
        return vector_store
