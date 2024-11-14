# coding: utf-8

from typing import ClassVar, Dict, List, Tuple
from fastapi import File, UploadFile
from fastapi.responses import FileResponse  # noqa: F401

from src.openapi_server.models.session import Session
from src.openapi_server.models.session_create_request import SessionCreateRequest
from src.openapi_server.models.session_list import SessionList
from src.openapi_server.models.session_update_request import SessionUpdateRequest


class BaseSessionApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSessionApi.subclasses = BaseSessionApi.subclasses + (cls,)

    def create_session(
        self,
        session_create_request: SessionCreateRequest,
    ) -> Session: ...

    def delete_session(
        self,
        session_id: int,
    ) -> None: ...

    def get_session(
        self,
        session_id: int,
    ) -> Session: ...

    def list_sessions(
        self,
    ) -> SessionList: ...

    def update_session(
        self,
        session_id: int,
        session_update_request: SessionUpdateRequest,
    ) -> Session: ...
