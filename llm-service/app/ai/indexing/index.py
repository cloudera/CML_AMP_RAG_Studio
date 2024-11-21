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
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generator, List, Type

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import BaseNode, Document, TextNode
from llama_index.readers.file import DocxReader

from ...ai.vector_stores.vector_store import VectorStore
from ...services.utils import batch_sequence, flatten_sequence
from .readers.csv import CSVReader
from .readers.json import JSONReader
from .readers.nop import NopReader
from .readers.pdf import PDFReader

logger = logging.getLogger(__name__)

READERS: Dict[str, Type[BaseReader]] = {
    ".pdf": PDFReader,
    ".txt": NopReader,
    ".md": NopReader,
    ".docx": DocxReader,
    ".csv": CSVReader,
    ".json": JSONReader,
}
CHUNKABLE_FILE_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


@dataclass
class NotSupportedFileExtensionError(Exception):
    file_extension: str


class Indexer:
    def __init__(
        self,
        data_source_id: int,
        splitter: SentenceSplitter,
        embedding_model: BaseEmbedding,
        chunks_vector_store: VectorStore,
    ):
        self.data_source_id = data_source_id
        self.splitter = splitter
        self.embedding_model = embedding_model
        self.chunks_vector_store = chunks_vector_store

    def index_file(self, file_path: Path, document_id: str) -> None:
        logger.debug(f"Indexing file: {file_path}")

        file_extension = os.path.splitext(file_path)[1]
        reader_cls = READERS.get(file_extension)
        if not reader_cls:
            raise NotSupportedFileExtensionError(file_extension)

        reader = reader_cls()

        logger.debug(f"Parsing file: {file_path}")

        documents = self._documents_in_file(reader, file_path, document_id)
        if file_extension in CHUNKABLE_FILE_EXTENSIONS:
            logger.debug(f"Chunking file: {file_path}")
            chunks = [
                chunk
                for document in documents
                for chunk in self._chunks_in_document(document)
            ]
        else:
            chunks = documents

        logger.debug(f"Embedding {len(chunks)} chunks")

        chunks_with_embeddings = flatten_sequence(self._compute_embeddings(chunks))

        acc = 0
        for chunk_batch in batch_sequence(chunks_with_embeddings, 1000):
            acc += len(chunk_batch)
            logger.debug(f"Adding {acc}/{len(chunks)} chunks to vector store")

            # We have to explicitly convert here even though the types are compatible (TextNode inherits from BaseNode)
            # because the "add" annotation uses List instead of Sequence. We need to use TextNode explicitly because
            # we're capturing "text".
            converted_chunks: List[BaseNode] = [chunk for chunk in chunk_batch]

            chunks_vector_store = self.chunks_vector_store.llama_vector_store()
            chunks_vector_store.add(converted_chunks)

        logger.debug(f"Indexing file: {file_path} completed")

    def _documents_in_file(
        self, reader: BaseReader, file_path: Path, document_id: str
    ) -> List[Document]:
        documents = reader.load_data(file_path)

        for i, document in enumerate(documents):
            document.id_ = document_id
            document.metadata["file_name"] = os.path.basename(file_path)
            document.metadata["document_id"] = document_id
            document.metadata["document_part_number"] = i
            document.metadata["data_source_id"] = self.data_source_id

        return documents

    def _chunks_in_document(self, document: Document) -> List[TextNode]:
        chunks = self.splitter.get_nodes_from_documents([document])

        for j, chunk in enumerate(chunks):
            chunk.metadata["file_name"] = document.metadata["file_name"]
            chunk.metadata["document_id"] = document.metadata["document_id"]
            chunk.metadata["document_part_number"] = document.metadata[
                "document_part_number"
            ]
            chunk.metadata["chunk_number"] = j
            chunk.metadata["data_source_id"] = document.metadata["data_source_id"]

        converted_chunks: List[TextNode] = []
        for chunk in chunks:
            assert isinstance(chunk, TextNode)
            converted_chunks.append(chunk)

        return converted_chunks

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
