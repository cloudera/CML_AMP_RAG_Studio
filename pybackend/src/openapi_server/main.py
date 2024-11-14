# coding: utf-8

"""
    RAG Studio API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 1.0.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from fastapi import FastAPI

from src.openapi_server.apis.data_source_api import router as DataSourceApiRouter
from src.openapi_server.apis.data_source_files_api import router as DataSourceFilesApiRouter
from src.openapi_server.apis.session_api import router as SessionApiRouter

app = FastAPI(
    title="RAG Studio API",
    description="No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)",
    version="1.0.0",
)

app.include_router(DataSourceApiRouter)
app.include_router(DataSourceFilesApiRouter)
app.include_router(SessionApiRouter)