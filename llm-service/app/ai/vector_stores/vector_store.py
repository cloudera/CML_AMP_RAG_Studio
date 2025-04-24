import time
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


pre_time = time.time()
import logging
print(f'import logging took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from abc import abstractmethod, ABCMeta
print(f'from abc import abstractmethod, ABCMeta took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from typing import Optional, List, cast
print(f'from typing import Optional, List, cast took {time.time() - start_time:.3f} seconds')




pre_time = time.time()
import umap
print(f'import umap took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from llama_index.core.base.embeddings.base import BaseEmbedding
print(f'from llama_index.core.base.embeddings.base import BaseEmbedding took {time.time() - start_time:.3f} seconds')


pre_time = time.time()
from llama_index.core.vector_stores.types import BasePydanticVectorStore
print(f'from llama_index.core.vector_stores.types import BasePydanticVectorStore took {time.time() - start_time:.3f} seconds')



logger = logging.getLogger(__name__)





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

    def visualize(

        self, user_query: Optional[str] = None

    ) -> list[tuple[tuple[float, float], str]]:

        """get a 2-d visualization of the vectors in the store"""



    @abstractmethod

    def get_embedding_model(self) -> BaseEmbedding:

        """get the embedding model used for this vector store"""



    def visualize_embeddings(

        self,

        embeddings: list[list[float]],

        filenames: list[str],

        user_query: Optional[str] = None,

    ) -> list[tuple[tuple[float, float], str]]:

        # trap an edge case where there are no records and umap blows up

        if len(embeddings) <= 2:

            return []

        if user_query:

            embedding_model = self.get_embedding_model()

            user_query_vector = embedding_model.get_query_embedding(user_query)

            embeddings.append(user_query_vector)

            filenames.append("USER_QUERY")

        reducer = umap.UMAP()

        try:

            reduced_embeddings: List[List[float]] = reducer.fit_transform(

                embeddings

            ).tolist()

            # todo: figure out how to satisfy mypy on this line

            return [

                (cast(tuple[float, float], tuple(coordinate)), filename)

                for filename, coordinate in zip(filenames, reduced_embeddings)

            ]

        except Exception as e:

            # Log the error

            logger.error(f"Error during UMAP transformation: {e}")

            return []
