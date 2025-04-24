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
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Generator, List

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, TextNode
from typing_extensions import Optional

from .base import BaseTextIndexer
from .readers.base_reader import ReaderConfig, ChunksResult
from ...ai.vector_stores.vector_store import VectorStore
from ...services.utils import batch_sequence, flatten_sequence

logger = logging.getLogger(__name__)


class EmbeddingIndexer(BaseTextIndexer):
    def __init__(
        self,
        data_source_id: int,
        splitter: SentenceSplitter,
        embedding_model: BaseEmbedding,
        chunks_vector_store: VectorStore,
        llm: Optional[LLM],
        reader_config: Optional[ReaderConfig] = None,
    ):
        super().__init__(data_source_id, reader_config)
        self.splitter = splitter
        self.embedding_model = embedding_model
        self.chunks_vector_store = chunks_vector_store
        self.llm = llm

    def index_file(self, file_path: Path, document_id: str) -> None:
        logger.debug(
            f"Indexing file: {file_path} with embedding model: {self.embedding_model.model_name}"
        )

        reader_cls = self._get_reader_class(file_path)

        reader = reader_cls(
            splitter=self.splitter,
            document_id=document_id,
            data_source_id=self.data_source_id,
            config=self.reader_config,
        )

        logger.debug(f"Parsing file: {file_path}")

        chunks: ChunksResult = reader.load_chunks(file_path)

        nodes: list[TextNode] = chunks.chunks
        if not nodes:
            logger.warning(f"No chunks found in file: {file_path}")
            return

        logger.debug(f"Embedding {len(nodes)} chunks")

        chunks_with_embeddings = flatten_sequence(self._compute_embeddings(nodes))

        acc = 0
        for chunk_batch in batch_sequence(chunks_with_embeddings, 1000):
            acc += len(chunk_batch)
            logger.debug(f"Adding {acc}/{len(nodes)} chunks to vector store")

            # We have to explicitly convert here even though the types are compatible (TextNode inherits from BaseNode)
            # because the "add" annotation uses List instead of Sequence. We need to use TextNode explicitly because
            # we're capturing "text".
            converted_chunks: List[BaseNode] = [chunk for chunk in chunk_batch]

            chunks_vector_store = self.chunks_vector_store.llama_vector_store()
            chunks_vector_store.add(converted_chunks)

        logger.debug(f"Indexing file: {file_path} completed")

    def _compute_embeddings(
        self, chunks: List[TextNode]
    ) -> Generator[List[TextNode], None, None]:
        batched_chunks = list(batch_sequence(chunks, 100))
        batched_texts = [[chunk.text for chunk in batch] for batch in batched_chunks]

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(
                    lambda b: (i, self.embedding_model.get_text_embedding_batch(b)),
                    batch,
                )
                for i, batch in enumerate(batched_texts)
            ]
            logger.debug(f"Waiting for {len(futures)} futures")
            for future in as_completed(futures):
                i, batch_embeddings = future.result()
                for chunk, embedding in zip(batched_chunks[i], batch_embeddings):
                    chunk.embedding = embedding
                yield batched_chunks[i]

print(f'ai/indexing/embedding_indexer.py took {time.time() - start_time:.3f} seconds to import')
