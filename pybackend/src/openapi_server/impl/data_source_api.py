from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from src.dal.data_source import DataSourceDAL
from src.db.provider import (
    DBConnectionProvider,
    SQLiteConnectionProviderSingleton,
    transaction,
)
from src.openapi_server.apis.data_source_api_base import BaseDataSourceApi
from src.openapi_server.impl.utils import raise_not_found_if_missing
from src.openapi_server.models.data_source import DataSource
from src.openapi_server.models.data_source_configuration import DataSourceConfiguration
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
        self._validate_configuration(data_source_create_request.configuration)

        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                now = datetime.now()
                user_id = ""

                id = DataSourceDAL.next_id(cursor)
                data_source = DataSource(
                    id=id,
                    name=data_source_create_request.name,
                    time_created=now,
                    time_updated=now,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                    configuration=data_source_create_request.configuration,
                    status=DataSourceStatus(
                        document_count=0,
                        total_doc_size=0,
                    ),
                )
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
        self._validate_configuration(data_source_update_request.configuration)

        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                now = datetime.now()
                user_id = ""

                data_source = raise_not_found_if_missing(
                    DataSourceDAL.get_data_source(cursor, data_source_id),
                    f"Data source with id {data_source_id} not found",
                )
                data_source.name = data_source_update_request.name
                data_source.configuration = data_source_update_request.configuration
                data_source.time_updated = now
                data_source.updated_by_id = user_id
                DataSourceDAL.save_data_source(cursor, data_source)
                return data_source

    def _validate_configuration(self, configuration: DataSourceConfiguration) -> None:
        if configuration.chunk_size <= 0:
            raise HTTPException(
                status_code=400, detail="Chunk size must be greater than 0"
            )


class DataSourceApiSingleton(BaseDataSourceApi):
    _instance: Optional[DataSourceApi] = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = DataSourceApi(SQLiteConnectionProviderSingleton())
        return cls._instance
