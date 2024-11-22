from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document, TextNode


class BaseReader(ABC):
    def __init__(
        self, splitter: SentenceSplitter, document_id: str, data_source_id: int
    ):
        self.splitter = splitter
        self.document_id = document_id
        self.data_source_id = data_source_id

    @abstractmethod
    def load_chunks(self, file_path: Path) -> List[TextNode]:
        pass

    def _add_document_metadata(self, node: TextNode, file_path: Path) -> None:
        node.metadata["file_name"] = file_path.name
        node.metadata["document_id"] = self.document_id
        node.metadata["data_source_id"] = self.data_source_id

    def _chunks_in_document(self, document: Document) -> List[TextNode]:
        chunks = self.splitter.get_nodes_from_documents([document])

        for i, chunk in enumerate(chunks):
            chunk.metadata["file_name"] = document.metadata["file_name"]
            chunk.metadata["document_id"] = document.metadata["document_id"]
            chunk.metadata["data_source_id"] = document.metadata["data_source_id"]
            chunk.metadata["chunk_number"] = i

        converted_chunks: List[TextNode] = []
        for chunk in chunks:
            assert isinstance(chunk, TextNode)
            converted_chunks.append(chunk)

        return converted_chunks
