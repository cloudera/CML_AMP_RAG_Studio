import logging
from typing import Set

from src.dal.session import SessionDAL
from src.db.provider import DBConnectionProvider, transaction
from src.log import setup_logger
from src.python_migration.python_client import PythonClient
from src.reconcilers.reconciler import Reconciler

logger = setup_logger(__name__)


class DeleteSessionReconciler(Reconciler):
    def __init__(
        self,
        db_connection_provider: DBConnectionProvider,
        python_client: PythonClient,
        **kwargs,
    ):
        super().__init__(logger=logger, **kwargs)
        self.db_connection_provider = db_connection_provider
        self.python_client = python_client

    def resync(self) -> None:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                sessions = SessionDAL.get_soft_deleted_sessions(cursor)
                for session in sessions:
                    self.submit(session.id)

    def reconcile(self, session_id: int) -> None:
        self.python_client.delete_session(session_id)
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                SessionDAL.hard_delete_session(cursor, session_id)
