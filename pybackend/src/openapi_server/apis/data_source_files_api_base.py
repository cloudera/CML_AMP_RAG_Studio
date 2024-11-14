# coding: utf-8

from typing import ClassVar, Dict, List, Tuple
from fastapi import File, UploadFile
from fastapi.responses import FileResponse  # noqa: F401

from src.openapi_server.models.data_source_file import DataSourceFile
from src.openapi_server.models.data_source_files import DataSourceFiles


class BaseDataSourceFilesApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseDataSourceFilesApi.subclasses = BaseDataSourceFilesApi.subclasses + (cls,)

    def delete_file_in_data_source(
        self,
        data_source_id: int,
        file_id: str,
    ) -> None: ...

    def get_file_in_data_source(
        self,
        data_source_id: int,
        file_id: str,
    ) -> FileResponse: ...

    def list_files_in_data_source(
        self,
        data_source_id: int,
    ) -> DataSourceFiles: ...

    def upload_file_to_data_source(
        self,
        data_source_id: int,
        file: UploadFile,
    ) -> DataSourceFile: ...
