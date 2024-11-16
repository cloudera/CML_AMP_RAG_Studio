import logging
from sqlite3 import Cursor
from typing import List, Optional

from src.dal.codec import decode_blob, encode_blob
from src.openapi_server.models.session import Session

logger = logging.getLogger(__name__)


class SessionDAL:
    @staticmethod
    def next_id(cursor: Cursor) -> int:
        cursor.execute("SELECT MAX(id) FROM sessions")
        last_id: Optional[int] = cursor.fetchone()[0]
        if last_id is None:
            return 1
        return last_id + 1

    @staticmethod
    def list_sessions(cursor: Cursor) -> List[Session]:
        cursor.execute("SELECT blob FROM sessions WHERE deleted = FALSE")
        return [SessionDAL._deserialize(row[0]) for row in cursor.fetchall()]

    @staticmethod
    def get_session(
        cursor: Cursor, session_id: int, allow_deleted: bool = False
    ) -> Optional[Session]:
        cursor.execute(
            "SELECT blob FROM sessions WHERE id = ? AND deleted = ?",
            (session_id, allow_deleted),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return SessionDAL._deserialize(row[0])

    @staticmethod
    def save_session(cursor: Cursor, session: Session) -> None:
        cursor.execute(
            "INSERT OR REPLACE INTO sessions (id, blob) VALUES (?, ?)",
            (session.id, SessionDAL._serialize(session)),
        )

    @staticmethod
    def soft_delete_session(cursor: Cursor, session_id: int) -> None:
        cursor.execute("UPDATE sessions SET deleted = TRUE WHERE id = ?", (session_id,))

    @staticmethod
    def hard_delete_session(cursor: Cursor, session_id: int) -> None:
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    @staticmethod
    def get_soft_deleted_sessions(cursor: Cursor) -> List[Session]:
        cursor.execute("SELECT blob FROM sessions WHERE deleted = TRUE")
        return [SessionDAL._deserialize(row[0]) for row in cursor.fetchall()]

    @staticmethod
    def _serialize(session: Session) -> bytes:
        return encode_blob(session)

    @staticmethod
    def _deserialize(data: bytes) -> Session:
        return decode_blob(Session, data)
