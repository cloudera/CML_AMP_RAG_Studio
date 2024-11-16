from dataclasses import dataclass
from typing import Any, Dict

import requests


@dataclass
class IndexConfiguration:
    chunk_size: int
    chunk_overlap_percentage: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap_percentage,
        }


@dataclass
class IndexRequest:
    s3_bucket_name: str
    s3_document_key: str
    data_source_id: int
    configuration: IndexConfiguration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "s3_bucket_name": self.s3_bucket_name,
            "s3_document_key": self.s3_document_key,
            "data_source_id": self.data_source_id,
            "configuration": self.configuration.to_dict(),
        }


@dataclass
class SummaryRequest:
    s3_bucket_name: str
    s3_document_key: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "s3_bucket_name": self.s3_bucket_name,
            "s3_document_key": self.s3_document_key,
        }


class PythonClient:
    def __init__(self, index_url: str) -> None:
        self.index_url = index_url
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def index_file(self, request: IndexRequest) -> None:
        try:
            response = self.session.post(
                f"{self.index_url}/download-and-index", json=request.to_dict()
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to index file: {str(e)}") from e

    def create_summary(self, request: SummaryRequest, data_source_id: int) -> str:
        try:
            response = self.session.post(
                f"{self.index_url}/data_sources/{data_source_id}/summarize-document",
                json=request.to_dict(),
            )
            response.raise_for_status()
            return str(response.text)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to create summary: {str(e)}") from e

    def delete_data_source(self, data_source_id: int) -> None:
        try:
            response = self.session.delete(
                f"{self.index_url}/data_sources/{data_source_id}"
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to delete data source: {str(e)}") from e

    def delete_document(self, data_source_id: int, document_id: str) -> None:
        try:
            response = self.session.delete(
                f"{self.index_url}/data_sources/{data_source_id}/documents/{document_id}"
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to delete document: {str(e)}") from e

    def delete_session(self, session_id: int) -> None:
        try:
            response = self.session.delete(f"{self.index_url}/sessions/{session_id}")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to delete session: {str(e)}") from e
