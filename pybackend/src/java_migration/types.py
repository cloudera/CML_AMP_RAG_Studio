from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from src.openapi_server.models.data_source import DataSource
from src.openapi_server.models.data_source_connection_type import (
    DataSourceConnectionType,
)
from src.openapi_server.models.data_source_file import DataSourceFile
from src.openapi_server.models.data_source_status import DataSourceStatus
from src.openapi_server.models.session import Session


class JavaConnectionType(Enum):
    MANUAL = "MANUAL"
    CDF = "CDF"
    API = "API"
    OTHER = "OTHER"


@dataclass
class JavaRagDataSource:
    id: int
    name: str
    chunk_size: int
    chunk_overlap_percent: int
    time_created: datetime
    time_updated: datetime
    created_by_id: str
    updated_by_id: str
    connection_type: JavaConnectionType
    document_count: Optional[int]
    total_doc_size: Optional[int]

    def to_model(self) -> DataSource:
        return DataSource(
            id=self.id,
            name=self.name,
            time_created=self.time_created,
            time_updated=self.time_updated,
            created_by_id=self.created_by_id,
            updated_by_id=self.updated_by_id,
            chunk_size=self.chunk_size,
            chunk_overlap_percent=self.chunk_overlap_percent,
            connection_type=DataSourceConnectionType(self.connection_type.value),
            status=DataSourceStatus(
                document_count=self.document_count or 0,
                total_doc_size=self.total_doc_size or 0,
            ),
        )


@dataclass
class JavaRagDocument:
    id: int
    file_name: str
    data_source_id: int
    document_id: str
    s3_path: str
    vector_upload_timestamp: Optional[datetime]
    size_in_bytes: int
    extension: str
    time_created: datetime
    time_updated: datetime
    created_by_id: str
    updated_by_id: str
    summary_creation_timestamp: Optional[datetime]

    def to_model(self) -> DataSourceFile:
        return DataSourceFile(
            id=str(self.id),
            time_created=self.time_created,
            time_updated=self.time_updated,
            created_by_id=self.created_by_id,
            updated_by_id=self.updated_by_id,
            filename=self.file_name,
            data_source_id=self.data_source_id,
            document_id=self.document_id,
            s3_path=self.s3_path,
            size_in_bytes=self.size_in_bytes,
            extension=self.extension,
            vector_upload_timestamp=self.vector_upload_timestamp,
            summary_creation_timestamp=self.summary_creation_timestamp,
        )


@dataclass
class JavaSession:
    id: int
    name: str
    data_source_ids: List[int]
    time_created: datetime
    time_updated: datetime
    created_by_id: str
    updated_by_id: str
    last_interaction_time: Optional[datetime]

    def to_model(self) -> Session:
        return Session(
            id=self.id,
            name=self.name,
            time_created=self.time_created,
            time_updated=self.time_updated,
            created_by_id=self.created_by_id,
            updated_by_id=self.updated_by_id,
            data_source_ids=self.data_source_ids,
            last_interaction_time=self.last_interaction_time,
        )
