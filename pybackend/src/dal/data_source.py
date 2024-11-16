from sqlite3 import Cursor
from typing import List, Optional

from src.dal.codec import decode_blob, encode_blob
from src.openapi_server.models.data_source import DataSource


class DataSourceDAL:
    @staticmethod
    def next_id(cursor: Cursor) -> int:
        cursor.execute("SELECT MAX(id) FROM data_sources")
        last_id: Optional[int] = cursor.fetchone()[0]
        if last_id is None:
            return 1
        return last_id + 1

    @staticmethod
    def list_data_sources(cursor: Cursor) -> List[DataSource]:
        cursor.execute(
            "SELECT blob FROM data_sources WHERE deleted = FALSE",
        )
        return [DataSourceDAL._deserialize(row[0]) for row in cursor.fetchall()]

    @staticmethod
    def get_data_source(
        cursor: Cursor, data_source_id: int, allow_deleted: bool = False
    ) -> Optional[DataSource]:
        cursor.execute(
            "SELECT blob FROM data_sources WHERE id = ? AND deleted = ?",
            (data_source_id, allow_deleted),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return DataSourceDAL._deserialize(row[0])

    @staticmethod
    def save_data_source(cursor: Cursor, data_source: DataSource) -> None:
        cursor.execute(
            "INSERT OR REPLACE INTO data_sources (id, blob) VALUES (?, ?)",
            (data_source.id, DataSourceDAL._serialize(data_source)),
        )

    @staticmethod
    def soft_delete_data_source(cursor: Cursor, data_source_id: int) -> None:
        cursor.execute(
            "UPDATE data_sources SET deleted = TRUE WHERE id = ?", (data_source_id,)
        )

    @staticmethod
    def hard_delete_data_source(cursor: Cursor, data_source_id: int) -> None:
        cursor.execute("DELETE FROM data_sources WHERE id = ?", (data_source_id,))

    @staticmethod
    def list_soft_deleted_data_sources_ids(cursor: Cursor) -> List[int]:
        cursor.execute(
            "SELECT id FROM data_sources WHERE deleted = TRUE",
        )
        return [row[0] for row in cursor.fetchall()]

    @staticmethod
    def _serialize(data_source: DataSource) -> bytes:
        return encode_blob(data_source)

    @staticmethod
    def _deserialize(data: bytes) -> DataSource:
        return decode_blob(DataSource, data)
