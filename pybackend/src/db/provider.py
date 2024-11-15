import os
import sqlite3
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from contextvars import ContextVar
from sqlite3 import Connection
from typing import Optional

from src.migration.datastore import SQLiteDatastore
from src.migration.migrator import Migrator


class DBConnectionProvider(ABC):
    @abstractmethod
    @contextmanager
    def connection(self):
        """Get a database connection."""
        pass


class TestConnectionProvider(DBConnectionProvider):
    def __init__(self):
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(":memory:")

    @contextmanager
    def connection(self):
        self._lock.acquire()
        try:
            yield self._connection
        finally:
            self._lock.release()


class SQLiteConnectionProvider(DBConnectionProvider):
    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def connection(self):
        yield sqlite3.connect(self.db_path)


@contextmanager
def transaction(conn: Connection):
    """Context manager for handling transactions."""
    cursor = conn.cursor()
    try:
        yield cursor  # Yield control back to the with block, where commands can be executed
        conn.commit()  # Commit if no exceptions were raised
    except Exception as e:
        conn.rollback()  # Roll back if an exception occurs
        print("Transaction failed:", e)
        raise  # Re-raise the exception after rollback
    finally:
        cursor.close()  # Close the cursor after completion
