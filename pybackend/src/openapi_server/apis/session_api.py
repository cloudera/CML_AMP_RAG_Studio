# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from src.openapi_server.apis.session_api_base import BaseSessionApi
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
from src.openapi_server.models.session import Session
from src.openapi_server.models.session_create_request import SessionCreateRequest
from src.openapi_server.models.session_list import SessionList
from src.openapi_server.models.session_update_request import SessionUpdateRequest


router = APIRouter(prefix="/api/v1")

ns_pkg = src.openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/rag/sessions",
    responses={
        200: {"model": Session, "description": "Session"},
    },
    tags=["session"],
    summary="Create a session",
    response_model_by_alias=True,
)
def create_session(
    session_create_request: SessionCreateRequest = Body(None, description=""),
) -> Session:
    if not BaseSessionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseSessionApi.subclasses[0]().create_session(session_create_request)


@router.delete(
    "/rag/sessions/{session_id}",
    responses={
        200: {"description": "Session deleted"},
    },
    tags=["session"],
    summary="Delete a session",
    response_model_by_alias=True,
)
def delete_session(
    session_id: int = Path(..., description=""),
) -> None:
    if not BaseSessionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseSessionApi.subclasses[0]().delete_session(session_id)


@router.get(
    "/rag/sessions/{session_id}",
    responses={
        200: {"model": Session, "description": "Session"},
    },
    tags=["session"],
    summary="Get a session",
    response_model_by_alias=True,
)
def get_session(
    session_id: int = Path(..., description=""),
) -> Session:
    if not BaseSessionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseSessionApi.subclasses[0]().get_session(session_id)


@router.get(
    "/rag/sessions",
    responses={
        200: {"model": SessionList, "description": "List of sessions"},
    },
    tags=["session"],
    summary="List sessions",
    response_model_by_alias=True,
)
def list_sessions(
) -> SessionList:
    if not BaseSessionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseSessionApi.subclasses[0]().list_sessions()


@router.put(
    "/rag/sessions/{session_id}",
    responses={
        200: {"model": Session, "description": "Session"},
    },
    tags=["session"],
    summary="Update a session",
    response_model_by_alias=True,
)
def update_session(
    session_id: int = Path(..., description=""),
    session_update_request: SessionUpdateRequest = Body(None, description=""),
) -> Session:
    if not BaseSessionApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return BaseSessionApi.subclasses[0]().update_session(session_id, session_update_request)
