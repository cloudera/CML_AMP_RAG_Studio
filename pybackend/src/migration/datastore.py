import re
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection
from typing import List

MIGRATION_STATE_TABLE = "migration_state"
MIGRATION_CONTENT_TABLE = "migration_content"

NAME_REGEX = re.compile(r"^(\d+)_[a-zA-Z0-9_-]+\.(up|down)\.sql$")


class MigrationContent:
    name: str
    id: int
    up: bool
    content: str

    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content
        match = NAME_REGEX.match(name)
        if match:
            self.id = int(match.group(1))
            self.up = match.group(2) == "up"
        else:
            raise ValueError(f"Invalid migration name: {name}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MigrationContent):
            return False
        return self.name == other.name and self.content == other.content

    def __lt__(self, other: "MigrationContent") -> bool:
        if self.id != other.id:
            return self.id < other.id
        return self.up < other.up

    def __repr__(self) -> str:
        return f"MigrationContent(name={self.name}, id={self.id}, up={self.up})"


@dataclass
class MigrationState:
    version: int
    dirty: bool


class Datastore(ABC):
    """Abstract base class for datastore migrations."""

    @abstractmethod
    def ensure_migration_state_table_exists(self) -> None:
        """
        Ensure the migration table exists.
        """
        pass

    @abstractmethod
    def get_migration_state(self) -> MigrationState:
        """Get the migration state."""
        pass

    @abstractmethod
    def update_migration_state(self, state: MigrationState) -> None:
        """Update the migration state."""
        pass

    @abstractmethod
    def ensure_migration_content_table_exists(self) -> None:
        """
        Ensure the migration content table exists.
        """
        pass

    @abstractmethod
    def get_migrations_from_db(self) -> List[MigrationContent]:
        """Get all migrations from the database."""
        pass

    @abstractmethod
    def get_migrations_from_disk(self) -> List[MigrationContent]:
        """Get all migrations from the disk."""
        pass

    @abstractmethod
    def update_migrations(self, migrations: List[MigrationContent]) -> None:
        """Update the migrations."""
        pass

    @abstractmethod
    def execute_migration(self, migration: MigrationContent) -> None:
        """Execute a migration."""
        pass


class SQLiteDatastore(Datastore):
    """Datastore implementation using SQLite."""

    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def ensure_migration_state_table_exists(self) -> None:
        """Create migration_state table if it doesn't exist."""
        self.connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MIGRATION_STATE_TABLE} (
                key INTEGER PRIMARY KEY,
                version INTEGER NOT NULL,
                dirty INTEGER NOT NULL CHECK (dirty IN (0, 1))
            )
            """
        )
        self.connection.commit()
        # If the table is empty, insert the initial row with (0, false)
        try:
            self.connection.execute(
                f"INSERT INTO {MIGRATION_STATE_TABLE} (key, version, dirty) VALUES (0, 0, 0)"
            )
            self.connection.commit()
        except sqlite3.IntegrityError:
            # Ignore integrity error if the row already exists, so we don't have to initialize
            pass

    def get_migration_state(self) -> MigrationState:
        cursor = self.connection.execute(
            f"SELECT version, dirty FROM {MIGRATION_STATE_TABLE} WHERE key = 0"
        )
        return MigrationState(*cursor.fetchone())

    def update_migration_state(self, state: MigrationState) -> None:
        self.connection.execute(
            f"INSERT OR REPLACE INTO {MIGRATION_STATE_TABLE} (key, version, dirty) VALUES (0, ?, ?)",
            (state.version, state.dirty),
        )
        self.connection.commit()

    def ensure_migration_content_table_exists(self) -> None:
        """Create migration_content table if it doesn't exist."""
        self.connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MIGRATION_CONTENT_TABLE} (
                name TEXT NOT NULL PRIMARY KEY,
                content TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def get_migrations_from_db(self) -> List[MigrationContent]:
        """Get all migrations from the database."""
        cursor = self.connection.execute(
            f"SELECT name, content FROM {MIGRATION_CONTENT_TABLE}"
        )
        return list(
            sorted([MigrationContent(name, content) for name, content in cursor])
        )

    def get_migrations_from_disk(self) -> List[MigrationContent]:
        """Get all migrations from the disk."""
        folder = Path(__file__).parent / "sqlite"
        migrations = []
        for file in folder.glob("*.sql"):
            with open(file, "r") as f:
                migrations.append(MigrationContent(file.name, f.read()))
        return list(sorted(migrations))

    def update_migrations(self, migrations: List[MigrationContent]) -> None:
        """Update the migrations."""
        migration_tuples = [(m.name, m.content) for m in migrations]

        self.connection.executemany(
            f"INSERT OR REPLACE INTO {MIGRATION_CONTENT_TABLE} (name, content) VALUES (?, ?)",
            migration_tuples,
        )
        self.connection.commit()

    def execute_migration(self, migration: MigrationContent) -> None:
        """Execute a migration."""
        sql = migration.content.strip()
        if sql:
            self.connection.execute(sql)
            self.connection.commit()
