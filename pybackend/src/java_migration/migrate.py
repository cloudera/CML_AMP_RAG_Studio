import os
from typing import Dict, List

from src.dal.data_source import DataSourceDAL
from src.dal.data_source_file import DataSourceFileDAL
from src.dal.session import SessionDAL
from src.db.provider import (
    DBConnectionProvider,
    transaction,
)
from src.java_migration.client import JavaClient
from src.java_migration.types import JavaRagDocument


class JavaMigrator:
    def __init__(
        self, client: JavaClient, db_connection_provider: DBConnectionProvider
    ):
        self.client = client
        self.db_connection_provider = db_connection_provider

    def migrate(self) -> None:
        # Load data sources
        data_sources = self.client.get_rag_data_sources()

        # Load documents
        documents: Dict[int, List[JavaRagDocument]] = {}
        for data_source in data_sources:
            documents[data_source.id] = self.client.get_rag_documents(data_source.id)

        # Load sessions
        sessions = self.client.get_rag_sessions()

        # Migrate data sources
        data_source_dal = DataSourceDAL()
        for data_source in data_sources:
            with self.db_connection_provider.connection() as connection:
                with transaction(connection) as cursor:
                    data_source_dal.save_data_source(cursor, data_source.to_model())

        # Migrate documents
        data_source_file_dal = DataSourceFileDAL()
        for documents_for_data_source in documents.values():
            for document in documents_for_data_source:
                with self.db_connection_provider.connection() as connection:
                    with transaction(connection) as cursor:
                        data_source_file_dal.save_data_source_file(
                            cursor, document.to_model()
                        )

        # Migrate sessions
        session_dal = SessionDAL()
        for session in sessions:
            with self.db_connection_provider.connection() as connection:
                with transaction(connection) as cursor:
                    session_dal.save_session(cursor, session.to_model())
