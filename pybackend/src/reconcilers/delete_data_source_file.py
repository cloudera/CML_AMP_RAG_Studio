import logging
from typing import Any, Optional

import boto3

from src.dal.data_source_file import DataSourceFileDAL
from src.db.provider import DBConnectionProvider, transaction
from src.log import setup_logger
from src.openapi_server.models.data_source_file import DataSourceFile
from src.python_migration.python_client import PythonClient
from src.reconcilers.reconciler import Reconciler

logger = setup_logger(__name__)


class DeleteDataSourceFileReconciler(Reconciler[str]):
    def __init__(
        self,
        db_connection_provider: DBConnectionProvider,
        python_client: PythonClient,
        s3_bucket_name: str,
        s3_client: boto3.client,
        **kwargs: Any,
    ) -> None:
        super().__init__(logger=logger, **kwargs)
        self.db_connection_provider = db_connection_provider
        self.python_client = python_client
        self.s3_bucket_name = s3_bucket_name
        self.s3_client = s3_client

    def resync(self) -> None:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                data_source_files = (
                    DataSourceFileDAL.get_soft_deleted_data_source_files(cursor)
                )
                for data_source_file in data_source_files:
                    self.submit(data_source_file.id)

    def reconcile(self, data_source_file_id: str) -> None:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                data_source_file: Optional[DataSourceFile] = (
                    DataSourceFileDAL.get_data_source_file(
                        cursor, data_source_file_id, allow_deleted=True
                    )
                )
                if data_source_file is None:
                    return

        self.python_client.delete_document(
            data_source_file.data_source_id, data_source_file.id
        )
        # Delete the file from s3
        self.s3_client.delete_object(
            Bucket=self.s3_bucket_name, Key=data_source_file.s3_path
        )

        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                DataSourceFileDAL.hard_delete_data_source_file(
                    cursor, data_source_file.id
                )
