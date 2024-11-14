from datetime import datetime

from src.dal.session import SessionDAL
from src.db.provider import DBConnectionProvider, transaction
from src.openapi_server.apis.session_api_base import BaseSessionApi
from src.openapi_server.impl.utils import raise_not_found_if_missing
from src.openapi_server.models.session import Session
from src.openapi_server.models.session_create_request import SessionCreateRequest
from src.openapi_server.models.session_list import SessionList
from src.openapi_server.models.session_update_request import SessionUpdateRequest


class SessionApi(BaseSessionApi):
    def __init__(self, db_connection_provider: DBConnectionProvider):
        self.db_connection_provider = db_connection_provider

    def create_session(
        self,
        session_create_request: SessionCreateRequest,
    ) -> Session:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                now = datetime.now()
                user_id = ""

                id = SessionDAL.next_id(cursor)
                session = Session(
                    id=id,
                    name=session_create_request.name,
                    time_created=now,
                    time_updated=now,
                    created_by_id=user_id,
                    updated_by_id=user_id,
                    last_interaction_time=None,
                    data_source_ids=session_create_request.data_source_ids,
                )
                SessionDAL.save_session(cursor, session)
                return session

    def delete_session(
        self,
        session_id: int,
    ) -> None:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                SessionDAL.soft_delete_session(cursor, session_id)

    def get_session(
        self,
        session_id: int,
    ) -> Session:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                return raise_not_found_if_missing(
                    SessionDAL.get_session(cursor, session_id),
                    f"Session with id {session_id} not found",
                )

    def list_sessions(
        self,
    ) -> SessionList:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                return SessionList(items=SessionDAL.list_sessions(cursor))

    def update_session(
        self,
        session_id: int,
        session_update_request: SessionUpdateRequest,
    ) -> Session:
        with self.db_connection_provider.connection() as connection:
            with transaction(connection) as cursor:
                now = datetime.now()
                user_id = ""

                session = raise_not_found_if_missing(
                    SessionDAL.get_session(cursor, session_id),
                    f"Session with id {session_id} not found",
                )
                session.name = session_update_request.name
                session.time_updated = now
                session.updated_by_id = user_id
                # TODO: update last_interaction_time?
                SessionDAL.save(cursor, session)
                return session
