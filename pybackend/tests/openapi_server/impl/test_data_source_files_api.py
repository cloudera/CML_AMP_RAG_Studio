import os
import tempfile
import time
import uuid
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock

import boto3
import pytest
from fastapi import HTTPException, UploadFile
from moto import mock_aws
from src.dal.data_source import DataSourceDAL
from src.db.provider import DBConnectionProvider, transaction
from src.openapi_server.impl.data_source_api import DataSourceApi
from src.openapi_server.impl.data_source_files_api import (
    DataSourceFilesApi,
    DataSourceFilesApiConfig,
)
from src.openapi_server.models.data_source import DataSource
from src.openapi_server.models.data_source_configuration import DataSourceConfiguration
from src.openapi_server.models.data_source_create_request import DataSourceCreateRequest
from src.openapi_server.models.data_source_status import DataSourceStatus


@pytest.fixture
def s3_client():
    """Mock S3 client using moto."""
    with mock_aws():
        s3 = boto3.client("s3")
        # Create test bucket
        s3.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        yield s3


@pytest.fixture
def api_config():
    return DataSourceFilesApiConfig(
        bucket_name="test-bucket", s3_path_prefix="test-prefix"
    )


@pytest.fixture
def mock_file():
    """Create a mock UploadFile."""
    content = b"test file content"
    file = MagicMock(spec=UploadFile)
    file.filename = "test.txt"
    file.size = len(content)
    file.file = BytesIO(content)
    return file


def test_upload_file_success(
    db_connection_provider: DBConnectionProvider, s3_client, api_config, mock_file
):
    temp_dir = tempfile.TemporaryDirectory()

    # Setup
    api = DataSourceFilesApi(
        db_connection_provider, api_config, s3_client, temp_dir.name
    )

    # Create test data source
    data_source = DataSourceApi(db_connection_provider).create_data_source(
        DataSourceCreateRequest(
            name="test source",
            configuration=DataSourceConfiguration(
                chunk_size=512, chunk_overlap_percent=10, connection_type="MANUAL"
            ),
        )
    )
    data_source_id = data_source.id

    # Execute
    result = api.upload_file_to_data_source(data_source_id, mock_file)

    # Verify
    assert result.filename == mock_file.filename
    assert result.size_in_bytes == mock_file.size
    assert result.data_source_id == data_source_id
    assert result.document_id is not None
    assert result.s3_path.startswith(f"{api_config.s3_path_prefix}/{data_source_id}/")


def test_upload_file_no_filename(db_connection_provider, s3_client, api_config):
    temp_dir = tempfile.TemporaryDirectory()

    api = DataSourceFilesApi(
        db_connection_provider, api_config, s3_client, temp_dir.name
    )

    # Create mock file without filename
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = None

    # Verify it raises exception
    with pytest.raises(HTTPException) as exc_info:
        api.upload_file_to_data_source(1, mock_file)
    assert exc_info.value.status_code == 400
    assert "File has no filename" in str(exc_info.value.detail)


def test_upload_file_nonexistent_datasource(
    db_connection_provider, s3_client, api_config, mock_file
):
    api = DataSourceFilesApi(db_connection_provider, api_config, s3_client, "/tmp")

    # Try uploading to non-existent data source
    with pytest.raises(HTTPException) as exc_info:
        api.upload_file_to_data_source(99999, mock_file)
    assert exc_info.value.status_code == 404
    assert "Data source with id 99999 not found" in str(exc_info.value.detail)


def test_download_file_success(
    db_connection_provider, s3_client, api_config, mock_file
):
    """Test successful file download."""
    temp_dir = tempfile.TemporaryDirectory()
    api = DataSourceFilesApi(
        db_connection_provider, api_config, s3_client, temp_dir.name
    )

    # Create test data source and upload a file
    data_source = DataSourceApi(db_connection_provider).create_data_source(
        DataSourceCreateRequest(
            name="test source",
            configuration=DataSourceConfiguration(
                chunk_size=512, chunk_overlap_percent=10, connection_type="MANUAL"
            ),
        )
    )
    uploaded_file = api.upload_file_to_data_source(data_source.id, mock_file)

    # Download the file
    response = api.download_file_in_data_source(data_source.id, uploaded_file.id)

    # Verify response
    assert response.filename == mock_file.filename
    assert response.headers["Content-Length"] == str(mock_file.size)
    assert (
        response.headers["Content-Disposition"]
        == f"attachment; filename={mock_file.filename}"
    )
    assert response.media_type == "application/octet-stream"
    assert os.path.exists(response.path)


def test_download_nonexistent_datasource(db_connection_provider, s3_client, api_config):
    """Test downloading from non-existent data source."""
    api = DataSourceFilesApi(db_connection_provider, api_config, s3_client, "/tmp")

    with pytest.raises(HTTPException) as exc_info:
        api.download_file_in_data_source(99999, "some-file-id")
    assert exc_info.value.status_code == 404
    assert "Data source with id 99999 not found" in str(exc_info.value.detail)


def test_download_nonexistent_file(db_connection_provider, s3_client, api_config):
    """Test downloading non-existent file."""
    # Create test data source
    data_source = DataSourceApi(db_connection_provider).create_data_source(
        DataSourceCreateRequest(
            name="test source",
            configuration=DataSourceConfiguration(
                chunk_size=512, chunk_overlap_percent=10, connection_type="MANUAL"
            ),
        )
    )

    api = DataSourceFilesApi(db_connection_provider, api_config, s3_client, "/tmp")

    with pytest.raises(HTTPException) as exc_info:
        api.download_file_in_data_source(data_source.id, "nonexistent-file-id")
    assert exc_info.value.status_code == 404
    assert "Data source file with id nonexistent-file-id not found" in str(
        exc_info.value.detail
    )


def test_download_cached_file(db_connection_provider, s3_client, api_config, mock_file):
    """Test downloading an already downloaded (cached) file."""
    temp_dir = tempfile.TemporaryDirectory()
    api = DataSourceFilesApi(
        db_connection_provider, api_config, s3_client, temp_dir.name
    )

    # Create test data source and upload a file
    data_source = DataSourceApi(db_connection_provider).create_data_source(
        DataSourceCreateRequest(
            name="test source",
            configuration=DataSourceConfiguration(
                chunk_size=512, chunk_overlap_percent=10, connection_type="MANUAL"
            ),
        )
    )
    uploaded_file = api.upload_file_to_data_source(data_source.id, mock_file)

    # Download file first time
    response1 = api.download_file_in_data_source(data_source.id, uploaded_file.id)
    first_modified_time = os.path.getmtime(response1.path)

    # Small delay to ensure modification time would be different
    time.sleep(0.1)

    # Download file second time (should use cached file)
    response2 = api.download_file_in_data_source(data_source.id, uploaded_file.id)
    second_modified_time = os.path.getmtime(response2.path)

    # Verify the file was accessed again (modification time updated)
    assert second_modified_time > first_modified_time
