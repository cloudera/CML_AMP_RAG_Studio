from datetime import datetime
from typing import Optional

from src.dal.data_source import DataSourceDAL
from src.dal.data_source_file import DataSourceFileDAL
from src.db.provider import DBConnectionProvider, transaction
from src.openapi_server.models.data_source_file import DataSourceFile
from src.python_migration.python_client import (
    IndexConfiguration,
    IndexRequest,
    PythonClient,
)
from src.reconcilers.reconciler import Reconciler


class IndexDataSourceFileReconciler(Reconciler):
    def __init__(
        self,
        db_connection_provider: DBConnectionProvider,
        python_client: PythonClient,
        s3_bucket_name: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.db_connection_provider = db_connection_provider
        self.python_client = python_client
        self.s3_bucket_name = s3_bucket_name

    def resync(self) -> None:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                data_source_files = (
                    DataSourceFileDAL.get_soft_deleted_data_source_files(cursor)
                )
                for data_source_file in data_source_files:
                    self.submit(data_source_file.id)

    def reconcile(self, data_source_file_id: int) -> None:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                data_source_file: Optional[DataSourceFile] = (
                    DataSourceFileDAL.get_data_source_file(cursor, data_source_file_id)
                )
                if data_source_file is None:
                    return
                data_source = DataSourceDAL.get_data_source(
                    cursor, data_source_file.data_source_id
                )
                if data_source is None:
                    return
                if data_source_file.vector_upload_timestamp is not None:
                    return

        self.python_client.index_file(
            IndexRequest(
                s3_bucket_name=self.s3_bucket_name,
                s3_document_key=data_source_file.s3_path,
                data_source_id=data_source_file.data_source_id,
                configuration=IndexConfiguration(
                    chunk_size=data_source.configuration.chunk_size,
                    chunk_overlap_percentage=data_source.configuration.chunk_overlap_percent,
                ),
            )
        )

        now = datetime.now()
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                data_source_file = DataSourceFileDAL.get_data_source_file(
                    cursor, data_source_file_id
                )
                if data_source_file is None:
                    return
                data_source_file.vector_upload_timestamp = now
                DataSourceFileDAL.save_data_source_file(cursor, data_source_file)
