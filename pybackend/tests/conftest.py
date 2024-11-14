import sqlite3
import sys
from pathlib import Path

import pytest
from src.db.provider import TestConnectionProvider
from src.migration.datastore import SQLiteDatastore
from src.migration.migrator import Migrator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def sqlite_connection():
    """Create a SQLite in-memory database connection for testing."""
    connection = sqlite3.connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def sqlite_datastore(sqlite_connection: sqlite3.Connection):
    """Create a SQLDatastore instance with an in-memory SQLite database."""
    datastore = SQLiteDatastore(sqlite_connection)
    return datastore


@pytest.fixture
def migrator(sqlite_datastore: SQLiteDatastore):
    return Migrator(sqlite_datastore)


@pytest.fixture(scope="function")
def db_connection_provider():
    provider = TestConnectionProvider()
    with provider.connection() as connection:
        datastore = SQLiteDatastore(connection)
        migrator = Migrator(datastore)
        migrator.perform_migration()

    return provider
