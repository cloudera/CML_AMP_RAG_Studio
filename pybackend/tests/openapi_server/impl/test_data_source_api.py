import pytest
from fastapi import HTTPException
from src.db.provider import DBConnectionProvider
from src.openapi_server.impl.data_source_api import DataSourceApi
from src.openapi_server.models.data_source_create_request import DataSourceCreateRequest
from src.openapi_server.models.data_source_update_request import DataSourceUpdateRequest


def test_create_data_source(db_connection_provider: DBConnectionProvider):
    data_source_api = DataSourceApi(db_connection_provider)
    name = "test-name"
    chunk_size = 512
    chunk_overlap_percent = 10
    connection_type = "MANUAL"

    create_request = DataSourceCreateRequest(
        name=name,
        chunk_size=chunk_size,
        chunk_overlap_percent=chunk_overlap_percent,
        connection_type=connection_type,
    )

    data_source = data_source_api.create_data_source(create_request)

    # Basic validations
    assert data_source.id is not None
    assert data_source.name == name
    assert data_source.chunk_size == chunk_size
    assert data_source.chunk_overlap_percent == chunk_overlap_percent
    assert data_source.connection_type == connection_type

    # Additional validations matching Java test
    assert data_source.time_created is not None
    assert data_source.time_updated is not None
    assert data_source.created_by_id == ""
    assert data_source.updated_by_id == ""
    assert data_source.status.document_count == 0
    assert data_source.status.total_doc_size == 0


def test_update_data_source(db_connection_provider: DBConnectionProvider):
    data_source_api = DataSourceApi(db_connection_provider)

    # Create initial data source
    original_name = "original-name"
    chunk_size = 1024
    chunk_overlap_percent = 20
    connection_type = "MANUAL"

    create_request = DataSourceCreateRequest(
        name=original_name,
        chunk_size=chunk_size,
        chunk_overlap_percent=chunk_overlap_percent,
        connection_type=connection_type,
    )
    data_source = data_source_api.create_data_source(create_request)

    # Update the name
    updated_name = "updated-name"
    update_request = DataSourceUpdateRequest(
        name=updated_name,
        chunk_size=chunk_size,
        chunk_overlap_percent=chunk_overlap_percent,
        connection_type=connection_type,
    )
    updated = data_source_api.update_data_source(data_source.id, update_request)

    # Verify the update
    assert updated.name == updated_name
    assert updated.id == data_source.id
    assert updated.chunk_size == chunk_size
    assert updated.chunk_overlap_percent == chunk_overlap_percent
    assert updated.connection_type == connection_type


def test_delete_data_source(db_connection_provider: DBConnectionProvider):
    data_source_api = DataSourceApi(db_connection_provider)
    create_request = DataSourceCreateRequest(
        name="test-name",
        chunk_size=1024,
        chunk_overlap_percent=20,
        connection_type="MANUAL",
    )

    data_source = data_source_api.create_data_source(create_request)
    data_source_api.delete_data_source(data_source.id)

    with pytest.raises(HTTPException) as exc_info:
        data_source_api.get_data_source(data_source.id)
    assert exc_info.value.status_code == 404


def test_get_data_sources(db_connection_provider: DBConnectionProvider):
    data_source_api = DataSourceApi(db_connection_provider)

    # Create first data source
    create_request1 = DataSourceCreateRequest(
        name="test1",
        chunk_size=1024,
        chunk_overlap_percent=20,
        connection_type="MANUAL",
    )
    data_source1 = data_source_api.create_data_source(create_request1)

    # Create second data source
    create_request2 = DataSourceCreateRequest(
        name="test2",
        chunk_size=512,
        chunk_overlap_percent=10,
        connection_type="MANUAL",
    )
    data_source2 = data_source_api.create_data_source(create_request2)

    # Get all data sources
    result = data_source_api.list_data_sources()

    # Verify we have at least the 2 data sources we created
    assert len(result.items) >= 2
    assert any(ds.id == data_source1.id for ds in result.items)
    assert any(ds.id == data_source2.id for ds in result.items)


def test_get_data_source_not_found(db_connection_provider: DBConnectionProvider):
    data_source_api = DataSourceApi(db_connection_provider)

    with pytest.raises(HTTPException) as exc_info:
        data_source_api.get_data_source(99999)
    assert exc_info.value.status_code == 404


def test_empty_chunk_size_not_allowed(db_connection_provider: DBConnectionProvider):
    data_source_api = DataSourceApi(db_connection_provider)

    # Create a data source with null chunk_size
    create_request = DataSourceCreateRequest(
        name="test-name",
        chunk_size=0,
        chunk_overlap_percent=20,
        connection_type="MANUAL",
    )

    # Assert that creating with null chunk_size raises HTTPException
    with pytest.raises(HTTPException) as exc_info:
        data_source_api.create_data_source(create_request)
    assert exc_info.value.status_code == 400  # Bad Request
