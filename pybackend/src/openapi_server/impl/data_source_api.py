from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from src.dal.data_source import DataSourceDAL
from src.db.provider import (
    DBConnectionProvider,
    transaction,
)
from src.openapi_server.apis.data_source_api_base import BaseDataSourceApi
from src.openapi_server.impl.utils import raise_not_found_if_missing
from src.openapi_server.models.data_source import DataSource
from src.openapi_server.models.data_source_create_request import DataSourceCreateRequest
from src.openapi_server.models.data_source_list import DataSourceList
from src.openapi_server.models.data_source_status import DataSourceStatus
from src.openapi_server.models.data_source_update_request import DataSourceUpdateRequest


class DataSourceApi:
    def __init__(self, db_connection_provider: DBConnectionProvider):
        self.db_connection_provider = db_connection_provider

    def create_data_source(
        self,
        data_source_create_request: DataSourceCreateRequest,
    ) -> DataSource:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                now = datetime.now()
                user_id = ""

                id = DataSourceDAL.next_id(cursor)
                chunk_overlap_percent = (
                    data_source_create_request.chunk_overlap_percent or 0
                )
                data_source = DataSource(
                    id=id,
                    name=data_source_create_request.name,
                    time_created=now,
                    time_updated=now,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                    connection_type=data_source_create_request.connection_type,
                    chunk_size=data_source_create_request.chunk_size,
                    chunk_overlap_percent=chunk_overlap_percent,
                    status=DataSourceStatus(
                        document_count=0,
                        total_doc_size=0,
                    ),
                )
                self._validate_configuration(data_source)
                DataSourceDAL.save_data_source(cursor, data_source)
                return data_source

    def delete_data_source(
        self,
        data_source_id: int,
    ) -> None:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                DataSourceDAL.soft_delete_data_source(cursor, data_source_id)

    def get_data_source(
        self,
        data_source_id: int,
    ) -> DataSource:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                return raise_not_found_if_missing(
                    DataSourceDAL.get_data_source(cursor, data_source_id),
                    f"Data source with id {data_source_id} not found",
                )

    def list_data_sources(
        self,
    ) -> DataSourceList:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                return DataSourceList(items=DataSourceDAL.list_data_sources(cursor))

    def update_data_source(
        self,
        data_source_id: int,
        data_source_update_request: DataSourceUpdateRequest,
    ) -> DataSource:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                now = datetime.now()
                user_id = ""

                data_source = raise_not_found_if_missing(
                    DataSourceDAL.get_data_source(cursor, data_source_id),
                    f"Data source with id {data_source_id} not found",
                )
                if data_source_update_request.name is not None:
                    data_source.name = data_source_update_request.name
                if data_source_update_request.connection_type is not None:
                    data_source.connection_type = (
                        data_source_update_request.connection_type
                    )
                if data_source_update_request.chunk_size is not None:
                    data_source.chunk_size = data_source_update_request.chunk_size
                if data_source_update_request.chunk_overlap_percent is not None:
                    data_source.chunk_overlap_percent = (
                        data_source_update_request.chunk_overlap_percent
                    )
                data_source.time_updated = now
                data_source.updated_by_id = user_id
                self._validate_configuration(data_source)

                DataSourceDAL.save_data_source(cursor, data_source)
                return data_source

    def _validate_configuration(self, data_source: DataSource) -> None:
        if data_source.chunk_size <= 0:
            raise HTTPException(
                status_code=400, detail="Chunk size must be greater than 0"
            )


class DataSourceApiSingleton(BaseDataSourceApi):
    _instance: Optional[DataSourceApi] = None

    def __new__(cls, **kwargs):
        if not cls._instance:
            cls._instance = DataSourceApi(**kwargs)
        return cls._instance