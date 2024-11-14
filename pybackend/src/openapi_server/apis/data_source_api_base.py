# coding: utf-8

from typing import ClassVar, Dict, List, Tuple
from fastapi import File, UploadFile
from fastapi.responses import FileResponse  # noqa: F401

from src.openapi_server.models.data_source import DataSource
from src.openapi_server.models.data_source_create_request import DataSourceCreateRequest
from src.openapi_server.models.data_source_list import DataSourceList
from src.openapi_server.models.data_source_update_request import DataSourceUpdateRequest


class BaseDataSourceApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseDataSourceApi.subclasses = BaseDataSourceApi.subclasses + (cls,)

    def create_data_source(
        self,
        data_source_create_request: DataSourceCreateRequest,
    ) -> DataSource: ...

    def delete_data_source(
        self,
        data_source_id: int,
    ) -> None: ...

    def get_data_source(
        self,
        data_source_id: int,
    ) -> DataSource: ...

    def list_data_sources(
        self,
    ) -> DataSourceList: ...

    def update_data_source(
        self,
        data_source_id: int,
        data_source_update_request: DataSourceUpdateRequest,
    ) -> DataSource: ...
