import pytest
from fastapi import HTTPException
from src.db.provider import DBConnectionProvider
from src.openapi_server.impl.session_api import SessionApi
from src.openapi_server.models.session_create_request import SessionCreateRequest


def test_create_session(db_connection_provider: DBConnectionProvider):
    session_api = SessionApi(db_connection_provider)
    session_name = "test"
    session_create_request = SessionCreateRequest(
        name=session_name, data_source_ids=[1, 2, 3]
    )

    # TODO: support user id

    session = session_api.create_session(session_create_request)

    # Basic validations
    assert session.id is not None
    assert session.name == session_name
    assert session.data_source_ids == [1, 2, 3]

    # Additional validations matching Java test
    assert session.time_created is not None
    assert session.time_updated is not None
    assert session.created_by_id == ""
    assert session.updated_by_id == ""
    assert session.last_interaction_time is None


def test_delete_session(db_connection_provider: DBConnectionProvider):
    session_api = SessionApi(db_connection_provider)
    session_name = "test"
    session_create_request = SessionCreateRequest(
        name=session_name, data_source_ids=[1, 2, 3]
    )

    session = session_api.create_session(session_create_request)
    session_api.delete_session(session.id)

    with pytest.raises(HTTPException) as exc_info:
        session_api.get_session(session.id)
    assert exc_info.value.status_code == 404


def test_get_sessions(db_connection_provider: DBConnectionProvider):
    session_api = SessionApi(db_connection_provider)

    # Create first session
    session_create_request1 = SessionCreateRequest(
        name="test", data_source_ids=[1, 2, 3]
    )
    session_api.create_session(session_create_request1)

    # Create second session
    session_create_request2 = SessionCreateRequest(
        name="test2", data_source_ids=[1, 2, 3]
    )
    session_api.create_session(session_create_request2)

    # Get all sessions
    result = session_api.list_sessions()

    # Verify we have at least the 2 sessions we created
    assert len(result.items) >= 2
