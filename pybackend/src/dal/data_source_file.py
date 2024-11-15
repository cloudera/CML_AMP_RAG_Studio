from sqlite3 import Cursor
from typing import List, Optional

from src.openapi_server.models.data_source_file import DataSourceFile


class DataSourceFileDAL:
    @staticmethod
    def list_data_source_files(
        cursor: Cursor, data_source_id: int
    ) -> List[DataSourceFile]:
        cursor.execute(
            "SELECT blob FROM data_source_files WHERE data_source_id = ? AND deleted = FALSE",
            (data_source_id,),
        )
        return [DataSourceFileDAL._deserialize(row[0]) for row in cursor.fetchall()]

    @staticmethod
    def get_data_source_file(
        cursor: Cursor, data_source_file_id: str
    ) -> Optional[DataSourceFile]:
        cursor.execute(
            "SELECT blob FROM data_source_files WHERE id = ? AND deleted = FALSE",
            (data_source_file_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return DataSourceFileDAL._deserialize(row[0])

    @staticmethod
    def save_data_source_file(cursor: Cursor, data_source_file: DataSourceFile) -> None:
        cursor.execute(
            "INSERT OR REPLACE INTO data_source_files (id, blob, data_source_id) VALUES (?, ?, ?)",
            (
                data_source_file.id,
                DataSourceFileDAL._serialize(data_source_file),
                data_source_file.data_source_id,
            ),
        )

    @staticmethod
    def soft_delete_data_source_file(cursor: Cursor, data_source_file_id: str) -> None:
        cursor.execute(
            "UPDATE data_source_files SET deleted = TRUE WHERE id = ?",
            (data_source_file_id,),
        )

    @staticmethod
    def hard_delete_data_source_file(cursor: Cursor, data_source_file_id: str) -> None:
        cursor.execute(
            "DELETE FROM data_source_files WHERE id = ?",
            (data_source_file_id,),
        )

    @staticmethod
    def get_soft_deleted_data_source_files(cursor: Cursor) -> List[DataSourceFile]:
        cursor.execute(
            "SELECT blob FROM data_source_files WHERE deleted = TRUE",
        )
        return [DataSourceFileDAL._deserialize(row[0]) for row in cursor.fetchall()]

    @staticmethod
    def _serialize(data_source_file: DataSourceFile) -> bytes:
        return data_source_file.model_dump_json().encode("utf-8")

    @staticmethod
    def _deserialize(data: bytes) -> DataSourceFile:
        return DataSourceFile.model_validate_json(data.decode("utf-8"))
