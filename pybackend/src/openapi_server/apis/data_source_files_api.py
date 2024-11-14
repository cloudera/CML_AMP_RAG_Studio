# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from src.openapi_server.apis.data_source_files_api_base import BaseDataSourceFilesApi
import src.openapi_server.impl

from fastapi.responses import FileResponse
from fastapi import File, UploadFile
from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from src.openapi_server.models.extra_models import TokenModel  # noqa: F401
from src.openapi_server.models.data_source_file import DataSourceFile
from src.openapi_server.models.data_source_files import DataSourceFiles


router = APIRouter(prefix="/api/v1")

ns_pkg = src.openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.delete(
    "/rag/data_sources/{data_source_id}/files/{file_id}",
    responses={
        204: {"description": "File deleted successfully"},
    },
    tags=["data_source_files"],
    summary="Delete a file in a data source",
    response_model_by_alias=True,
)
def delete_file_in_data_source(
    data_source_id: int = Path(..., description=""),
    file_id: str = Path(..., description="The ID of the file to delete"),
) -> None:
    if not BaseDataSourceFilesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseDataSourceFilesApi.subclasses[0]().delete_file_in_data_source(data_source_id, file_id)


@router.get(
    "/rag/data_sources/{data_source_id}/files/{file_id}",
    response_class=FileResponse,
    tags=["data_source_files"],
    summary="Get a file in a data source",
    response_model_by_alias=True,
)
def get_file_in_data_source(
    data_source_id: int = Path(..., description=""),
    file_id: str = Path(..., description="The ID of the file to get"),
) -> FileResponse:
    if not BaseDataSourceFilesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseDataSourceFilesApi.subclasses[0]().get_file_in_data_source(data_source_id, file_id)


@router.get(
    "/rag/data_sources/{data_source_id}/files",
    responses={
        200: {"model": DataSourceFiles, "description": "Files retrieved successfully"},
    },
    tags=["data_source_files"],
    summary="List files in a data source",
    response_model_by_alias=True,
)
def list_files_in_data_source(
    data_source_id: int = Path(..., description="The ID of the data source to get the files from"),
) -> DataSourceFiles:
    if not BaseDataSourceFilesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseDataSourceFilesApi.subclasses[0]().list_files_in_data_source(data_source_id)


@router.post(
    "/rag/data_sources/{data_source_id}/files",
    responses={
        200: {"model": DataSourceFile, "description": "File uploaded successfully"},
    },
    tags=["data_source_files"],
    summary="Upload a file to a data source",
    response_model_by_alias=True,
)
def upload_file_to_data_source(
    data_source_id: int = Path(..., description="The ID of the data source to upload the file to"),
    file: UploadFile = File(..., description="The file to upload"),
) -> DataSourceFile:
    if not BaseDataSourceFilesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseDataSourceFilesApi.subclasses[0]().upload_file_to_data_source(data_source_id, file)
