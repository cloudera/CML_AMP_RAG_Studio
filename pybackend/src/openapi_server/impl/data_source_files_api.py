import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import boto3
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.dal.data_source import DataSourceDAL
from src.dal.data_source_file import DataSourceFileDAL
from src.db.provider import (
    DBConnectionProvider,
    transaction,
)
from src.openapi_server.apis.data_source_files_api_base import BaseDataSourceFilesApi
from src.openapi_server.impl.utils import raise_not_found_if_missing
from src.openapi_server.models.data_source_file import DataSourceFile
from src.openapi_server.models.data_source_files import DataSourceFiles


@dataclass
class DataSourceFilesApiConfig:
    bucket_name: str
    s3_path_prefix: str


class DataSourceFilesApi:
    def __init__(
        self,
        db_connection_provider: DBConnectionProvider,
        config: DataSourceFilesApiConfig,
        s3_client: boto3.client,
        files_dir: str,
    ):
        self.db_connection_provider = db_connection_provider
        self.config = config
        self.s3_client = s3_client
        self.files_dir = files_dir
        os.makedirs(self.files_dir, exist_ok=True)

    def delete_file_in_data_source(
        self,
        data_source_id: int,
        file_id: str,
    ) -> None:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                now = datetime.now()
                user_id = ""

                data_source = raise_not_found_if_missing(
                    DataSourceDAL.get_data_source(cursor, data_source_id),
                    f"Data source with id {data_source_id} not found",
                )
                data_source_file = raise_not_found_if_missing(
                    DataSourceFileDAL.get_data_source_file(cursor, file_id),
                    f"Data source file with id {file_id} not found",
                )
                DataSourceFileDAL.soft_delete_data_source_file(cursor, file_id)

                data_source.status.document_count -= 1
                data_source.status.total_doc_size -= data_source_file.size_in_bytes
                data_source.time_updated = now
                data_source.updated_by_id = user_id
                DataSourceDAL.save_data_source(cursor, data_source)

    def get_file_in_data_source(
        self,
        data_source_id: int,
        file_id: str,
    ) -> DataSourceFile:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                return raise_not_found_if_missing(
                    DataSourceFileDAL.get_data_source_file(cursor, file_id),
                    f"Data source file with id {file_id} not found",
                )

    def list_files_in_data_source(
        self,
        data_source_id: int,
    ) -> DataSourceFiles:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                return DataSourceFiles(
                    items=DataSourceFileDAL.list_data_source_files(
                        cursor, data_source_id
                    )
                )

    def upload_file_to_data_source(
        self,
        data_source_id: int,
        file: UploadFile,
    ) -> DataSourceFile:
        if file.filename is None:
            raise HTTPException(status_code=400, detail="File has no filename")

        # Check datasource exists
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                raise_not_found_if_missing(
                    DataSourceDAL.get_data_source(cursor, data_source_id),
                    f"Data source with id {data_source_id} not found",
                )

        id = str(uuid.uuid4())
        s3_path = self._s3_path(data_source_id, id)

        # Upload file to S3
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        with open(temp_file.name, "wb") as f:
            f.write(file.file.read())
        self.s3_client.upload_file(
            temp_file.name,
            self.config.bucket_name,
            s3_path,
            ExtraArgs={"Metadata": {"originalfilename": file.filename}},
        )

        # Save file metadata to DB
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                now = datetime.now()
                user_id = ""

                data_source = raise_not_found_if_missing(
                    DataSourceDAL.get_data_source(cursor, data_source_id),
                    f"Data source with id {data_source_id} not found",
                )
                data_source.status.document_count += 1
                data_source.status.total_doc_size += file.size or 0
                data_source.time_updated = now
                data_source.updated_by_id = user_id
                DataSourceDAL.save_data_source(cursor, data_source)

                extension = file.filename.split(".")[-1]
                if extension == file.filename:
                    extension = ""

                data_source_file = DataSourceFile(
                    id=id,
                    time_created=now,
                    time_updated=now,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                    filename=file.filename,
                    data_source_id=data_source_id,
                    document_id=id,  # ??
                    s3_path=s3_path,
                    size_in_bytes=file.size or 0,
                    extension=extension,
                    summary_creation_timestamp=None,
                    vector_upload_timestamp=None,
                )
                DataSourceFileDAL.save_data_source_file(cursor, data_source_file)
                return data_source_file

    def download_file_in_data_source(
        self,
        data_source_id: int,
        file_id: str,
    ) -> FileResponse:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                raise_not_found_if_missing(
                    DataSourceDAL.get_data_source(cursor, data_source_id),
                    f"Data source with id {data_source_id} not found",
                )
                data_source_file = raise_not_found_if_missing(
                    DataSourceFileDAL.get_data_source_file(cursor, file_id),
                    f"Data source file with id {file_id} not found",
                )

        # Check if the file is already downloaded
        file_path = os.path.join(self.files_dir, file_id)
        if not os.path.exists(file_path):
            # Download file from S3
            self.s3_client.download_file(
                self.config.bucket_name, data_source_file.s3_path, file_path
            )
        else:
            # Update the modified time to now
            now = datetime.now().timestamp()
            os.utime(file_path, (now, now))

        # Return the file
        headers = {
            "Content-Disposition": f"attachment; filename={data_source_file.filename}",
            "Content-Length": str(data_source_file.size_in_bytes),
        }
        return FileResponse(
            file_path,
            filename=data_source_file.filename,
            media_type="application/octet-stream",
            headers=headers,
        )

    def _s3_path(self, data_source_id: int, file_id: str) -> str:
        return f"{self.config.s3_path_prefix}/{data_source_id}/{file_id}"


class DataSourceFilesApiSingleton(BaseDataSourceFilesApi):  # type: ignore
    _instance: Optional[DataSourceFilesApi] = None

    def __new__(cls, **kwargs) -> DataSourceFilesApi:  # type: ignore
        if not cls._instance:
            cls._instance = DataSourceFilesApi(**kwargs)
        return cls._instance
