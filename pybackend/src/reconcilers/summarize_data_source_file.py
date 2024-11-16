from datetime import datetime
from typing import Any, Optional

from src.dal.data_source import DataSourceDAL
from src.dal.data_source_file import DataSourceFileDAL
from src.db.provider import DBConnectionProvider, transaction
from src.log import setup_logger
from src.openapi_server.models.data_source_file import DataSourceFile
from src.python_migration.python_client import (
    PythonClient,
    SummaryRequest,
)
from src.reconcilers.reconciler import Reconciler

logger = setup_logger(__name__)


class SummarizeDataSourceFileReconciler(Reconciler[str]):
    def __init__(
        self,
        db_connection_provider: DBConnectionProvider,
        python_client: PythonClient,
        s3_bucket_name: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(logger=logger, **kwargs)
        self.db_connection_provider = db_connection_provider
        self.python_client = python_client
        self.s3_bucket_name = s3_bucket_name

    def resync(self) -> None:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                ids = DataSourceFileDAL.list_ids_to_summarize(cursor)
                for id in ids:
                    self.submit(id)

    def reconcile(self, data_source_file_id: str) -> None:
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
                if data_source_file.summary_creation_timestamp is not None:
                    return

        self.python_client.create_summary(
            SummaryRequest(
                s3_bucket_name=self.s3_bucket_name,
                s3_document_key=data_source_file.s3_path,
            ),
            data_source_id=data_source_file.data_source_id,
        )

        now = datetime.now()
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                data_source_file = DataSourceFileDAL.get_data_source_file(
                    cursor, data_source_file_id
                )
                if data_source_file is None:
                    return
                data_source_file.summary_creation_timestamp = now
                DataSourceFileDAL.save_data_source_file(cursor, data_source_file)
