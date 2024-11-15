import os

from src.dal.data_source import DataSourceDAL
from src.dal.data_source_file import DataSourceFileDAL
from src.dal.session import SessionDAL
from src.db.provider import (
    DBConnectionProvider,
    SQLiteConnectionProviderSingleton,
    transaction,
)
from src.java_migration.client import JavaClient


class JavaMigrator:
    def __init__(
        self, client: JavaClient, db_connection_provider: DBConnectionProvider
    ):
        self.client = client
        self.db_connection_provider = db_connection_provider

    def migrate(self):
        # Load data sources
        data_sources = self.client.get_rag_data_sources()

        # Load documents
        documents = {}
        for data_source in data_sources:
            documents[data_source.id] = self.client.get_rag_documents(data_source.id)

        # Load sessions
        sessions = self.client.get_rag_sessions()

        # Migrate data sources
        dal = DataSourceDAL()
        for data_source in data_sources:
            with self.db_connection_provider.connection() as connection:
                with transaction(connection) as cursor:
                    dal.save_data_source(cursor, data_source.to_model())

        # Migrate documents
        dal = DataSourceFileDAL()
        for documents in documents.values():
            for document in documents:
                with self.db_connection_provider.connection() as connection:
                    with transaction(connection) as cursor:
                        dal.save_data_source_file(cursor, document.to_model())

        # Migrate sessions
        dal = SessionDAL()
        for session in sessions:
            with self.db_connection_provider.connection() as connection:
                with transaction(connection) as cursor:
                    dal.save_session(cursor, session.to_model())
