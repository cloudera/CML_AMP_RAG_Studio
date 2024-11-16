import logging
from typing import Any, Set

from src.dal.data_source import DataSourceDAL
from src.dal.data_source_file import DataSourceFileDAL
from src.db.provider import DBConnectionProvider, transaction
from src.log import setup_logger
from src.python_migration.python_client import PythonClient
from src.reconcilers.reconciler import Reconciler

logger = setup_logger(__name__)


class DeleteDataSourceReconciler(Reconciler[int]):
    def __init__(
        self,
        db_connection_provider: DBConnectionProvider,
        python_client: PythonClient,
        **kwargs: Any,
    ) -> None:
        super().__init__(logger=logger, **kwargs)
        self.db_connection_provider = db_connection_provider
        self.python_client = python_client

    def resync(self) -> None:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                data_sources = DataSourceDAL.get_soft_deleted_data_sources(cursor)
                for data_source in data_sources:
                    self.submit(data_source.id)

    def reconcile(self, data_source_id: int) -> None:
        self.python_client.delete_data_source(data_source_id)
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                DataSourceDAL.hard_delete_data_source(cursor, data_source_id)

                data_source_files = DataSourceFileDAL.list_data_source_files(
                    cursor, data_source_id
                )
                for data_source_file in data_source_files:
                    DataSourceFileDAL.soft_delete_data_source_file(
                        cursor, data_source_file.id
                    )
