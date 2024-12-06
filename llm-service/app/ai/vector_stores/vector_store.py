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

from abc import abstractmethod, ABCMeta
from typing import Optional

from llama_index.core.vector_stores.types import BasePydanticVectorStore


class VectorStore(metaclass=ABCMeta):
    """RAG Studio Vector Store functionality. Implementations of this should house the vectors for a single document collection."""

    @abstractmethod
    def size(self) -> Optional[int]:
        """
        If the collection does not exist, return None
        """

    @abstractmethod
    def delete(self) -> None:
        """Delete the vector store"""

    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        """Delete a single document from the vector store"""

    @abstractmethod
    def llama_vector_store(self) -> BasePydanticVectorStore:
        """Access the underlying llama-index vector store implementation"""

    @abstractmethod
    def exists(self) -> bool:
        """Does the vector store exist?"""

    @abstractmethod
    def visualize(self, user_query: Optional[str] = None) -> list[tuple[tuple[float,float], str]]:
        """get a 2-d visualization of the vectors in the store"""

    @abstractmethod
    def get_embedding_model(self):
        """get the embedding model used for this vector store"""
