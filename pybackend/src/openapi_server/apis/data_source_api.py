# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from src.openapi_server.apis.data_source_api_base import BaseDataSourceApi
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
from src.openapi_server.models.data_source import DataSource
from src.openapi_server.models.data_source_create_request import DataSourceCreateRequest
from src.openapi_server.models.data_source_list import DataSourceList
from src.openapi_server.models.data_source_update_request import DataSourceUpdateRequest


router = APIRouter(prefix="/api/v1")

ns_pkg = src.openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/rag/data_sources",
    responses={
        200: {"model": DataSource, "description": "Data source"},
    },
    tags=["data_source"],
    summary="Create a data source",
    response_model_by_alias=True,
)
def create_data_source(
    data_source_create_request: DataSourceCreateRequest = Body(None, description=""),
) -> DataSource:
    if not BaseDataSourceApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseDataSourceApi.subclasses[0]().create_data_source(data_source_create_request)


@router.delete(
    "/rag/data_sources/{data_source_id}",
    responses={
        200: {"description": "Data source deleted"},
    },
    tags=["data_source"],
    summary="Delete a data source",
    response_model_by_alias=True,
)
def delete_data_source(
    data_source_id: int = Path(..., description=""),
) -> None:
    if not BaseDataSourceApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseDataSourceApi.subclasses[0]().delete_data_source(data_source_id)


@router.get(
    "/rag/data_sources/{data_source_id}",
    responses={
        200: {"model": DataSource, "description": "Data source"},
    },
    tags=["data_source"],
    summary="Get a data source",
    response_model_by_alias=True,
)
def get_data_source(
    data_source_id: int = Path(..., description=""),
) -> DataSource:
    if not BaseDataSourceApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseDataSourceApi.subclasses[0]().get_data_source(data_source_id)


@router.get(
    "/rag/data_sources",
    responses={
        200: {"model": DataSourceList, "description": "List of data sources"},
    },
    tags=["data_source"],
    summary="List data sources",
    response_model_by_alias=True,
)
def list_data_sources(
) -> DataSourceList:
    if not BaseDataSourceApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseDataSourceApi.subclasses[0]().list_data_sources()


@router.put(
    "/rag/data_sources/{data_source_id}",
    responses={
        200: {"model": DataSource, "description": "Data source"},
    },
    tags=["data_source"],
    summary="Update a data source",
    response_model_by_alias=True,
)
def update_data_source(
    data_source_id: int = Path(..., description=""),
    data_source_update_request: DataSourceUpdateRequest = Body(None, description=""),
) -> DataSource:
    if not BaseDataSourceApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseDataSourceApi.subclasses[0]().update_data_source(data_source_id, data_source_update_request)
