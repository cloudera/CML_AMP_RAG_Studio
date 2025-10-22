import functools
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

from detect_secrets.core.secrets_collection import SecretsCollection
from detect_secrets.settings import default_settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document, TextNode, BaseNode
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine


@functools.cache
def _get_analyzer() -> AnalyzerEngine:
    """Cached analyzer engine to reuse compiled regex patterns."""
    return AnalyzerEngine()


@functools.cache
def _get_anonymizer() -> AnonymizerEngine:
    """Cached anonymizer engine to reuse compiled patterns."""
    return AnonymizerEngine()  # type: ignore[no-untyped-call]


@functools.lru_cache(maxsize=1)
def _get_secret_collection() -> SecretsCollection:
    """Cached secrets collection to reuse compiled regex patterns."""
    with default_settings():
        return SecretsCollection()


@dataclass
class ReaderConfig:
    block_secrets: bool = False
    anonymize_pii: bool = False


@dataclass
class ChunksResult:
    chunks: List[TextNode] = field(default_factory=list)
    # If present, the chunks contained secrets and the chunks should be empty
    secret_types: Optional[Set[str]] = None
    # If true, the chunks contained PII and the chunks contain anonymized text
    pii_found: bool = False


class BaseReader(ABC):
    def __init__(
        self,
        splitter: SentenceSplitter,
        document_id: str,
        data_source_id: int,
        config: Optional[ReaderConfig] = None,
    ):
        self.splitter = splitter
        self.document_id = document_id
        self.data_source_id = data_source_id
        self.config = config or ReaderConfig()

    @abstractmethod
    def load_chunks(self, file_path: Path) -> ChunksResult:
        pass

    def _add_document_metadata(self, node: BaseNode, file_path: Path) -> None:
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

    def _block_secrets(self, chunks: List[str]) -> Optional[Set[str]]:
        if not self.config.block_secrets:
            return None

        # Create a fresh collection each time since clear() doesn't exist
        # but still benefit from cached settings/plugins via default_settings()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = []
            for i, chunk in enumerate(chunks):
                path = os.path.join(tmpdir, f"chunk_{i}.txt")
                with open(path, "w") as f:
                    f.write(chunk)
                paths.append(path)

            secrets_collection = _get_secret_collection()
            with default_settings():
                secrets_collection.scan_files(*paths)

        secrets_json = secrets_collection.json()

        ret = set()
        for secrets in secrets_json.values():
            for secret in secrets:
                ret.add(secret.type)

        return ret

    def _anonymize_pii(self, text: str) -> Optional[str]:
        if not self.config.anonymize_pii:
            return None

        analyzer = _get_analyzer()

        # TODO: support other languages
        results = analyzer.analyze(text=text, entities=None, language="en")

        anonymizer = _get_anonymizer()

        anonymized_text = anonymizer.anonymize(text=text, analyzer_results=results)  # type: ignore[arg-type]
        if anonymized_text.text == text:
            return None

        return anonymized_text.text
