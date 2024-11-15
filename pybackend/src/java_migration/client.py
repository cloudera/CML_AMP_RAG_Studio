from typing import List

import requests
from src.java_migration.types import JavaRagDataSource, JavaRagDocument, JavaSession


class JavaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_rag_data_sources(self) -> List[JavaRagDataSource]:
        response = requests.get(f"{self.base_url}/api/v1/rag/dataSources")
        return [JavaRagDataSource(**data) for data in response.json()]

    def get_rag_documents(self, data_source_id: int) -> List[JavaRagDocument]:
        response = requests.get(
            f"{self.base_url}/api/v1/rag/dataSources/{data_source_id}/files"
        )
        return [JavaRagDocument(**data) for data in response.json()]

    def get_rag_sessions(self) -> List[JavaSession]:
        response = requests.get(f"{self.base_url}/api/v1/rag/sessions")
        return [JavaSession(**data) for data in response.json()]
