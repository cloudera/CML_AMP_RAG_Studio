# ##############################################################################
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#  NOTE: Cloudera open source products are modular software products
#  made up of hundreds of individual components, each of which was
#  individually copyrighted.  Each Cloudera open source product is a
#  collective work under U.S. Copyright Law. Your license to use the
#  collective work is as provided in your written agreement with
#  Cloudera.  Used apart from the collective work, this file is
#  licensed for your use pursuant to the open source license
#  identified above.
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
#  contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
#  KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
#  WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
#  IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
#  AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
#  ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
#  OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
#  CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
#  RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
#  BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
#  DATA.
# ##############################################################################

import os
import pathlib
import uuid
from collections.abc import Iterator
from typing import Any, Sequence

import boto3
import pytest
from fastapi.testclient import TestClient
from llama_index.core.base.embeddings.base import BaseEmbedding, Embedding
from llama_index.core.base.llms.types import CompletionResponseAsyncGen, ChatMessage, ChatResponseAsyncGen, \
    CompletionResponse, ChatResponse, CompletionResponseGen, ChatResponseGen, LLMMetadata
from llama_index.core.llms import LLM
from moto import mock_aws
from pydantic import Field

from app.main import app
from app.services import models, rag_vector_store
from app.services.rag_qdrant_vector_store import RagQdrantVectorStore
from app.services.utils import get_last_segment

@pytest.fixture
def aws_region() -> str:
    return os.environ.get("AWS_DEFAULT_REGION", "us-west-2")


@pytest.fixture(autouse=True)
def databases_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> str:
    databases_dir: str = str(tmp_path / "databases")
    monkeypatch.setenv("RAG_DATABASES_DIR", databases_dir)
    return databases_dir


@pytest.fixture
def s3(
        monkeypatch: pytest.MonkeyPatch,
) -> Iterator["s3.ServiceResource"]:
    """Mock all S3 interactions."""

    with mock_aws():
        yield boto3.resource("s3")


@pytest.fixture
def document_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def data_source_id() -> int:
    return -1


@pytest.fixture
def index_document_request_body(data_source_id, s3_object) -> dict[str, Any]:
    return {
        "document_id": get_last_segment(s3_object.key),
        "data_source_id": data_source_id,
        "s3_bucket_name": s3_object.bucket_name,
        "s3_document_key": s3_object.key,
        "configuration": {
            "chunk_size": 512,
            "chunk_overlap": 10,
        },
    }


class DummyLlm(LLM):
    completion_response = Field("this is a completion response")
    chat_response = Field("this is a chat response")

    def __init__(self, completion_response: str = "this is a completion response", chat_response: str = "hello"):
        super().__init__()
        self.completion_response = completion_response
        self.chat_response = chat_response

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata()

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        return ChatResponse(message=ChatMessage.from_str(self.chat_response))

    def complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        return CompletionResponse(text=self.completion_response)

    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseGen:
        pass

    def stream_complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponseGen:
        pass

    async def achat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        pass

    async def acomplete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        pass

    async def astream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseAsyncGen:
        pass

    async def astream_complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponseAsyncGen:
        pass


class DummyEmbeddingModel(BaseEmbedding):
    def _get_query_embedding(self, query: str) -> Embedding:
        return [0.1] * 1024

    async def _aget_query_embedding(self, query: str) -> Embedding:
        return [0.1] * 1024

    def _get_text_embedding(self, text: str) -> Embedding:
        return [0.1] * 1024


# We're hacking our vector stores to run in-memory. Since they are in memory, we need
# to be sure to return the same instance for the same data source id
table_name_to_vector_store = {}


def _get_vector_store_instance(data_source_id: int, table_prefix: str) -> RagQdrantVectorStore:
    if data_source_id in table_name_to_vector_store:
        return table_name_to_vector_store[data_source_id]
    res = RagQdrantVectorStore(table_name=f"{table_prefix}{data_source_id}", memory_store=True)
    table_name_to_vector_store[data_source_id] = res
    return res


@pytest.fixture(autouse=True)
def vector_store(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(rag_vector_store, 'create_rag_vector_store',
                        lambda ds_id: _get_vector_store_instance(ds_id, "index_"))


@pytest.fixture(autouse=True)
def summary_vector_store(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(rag_vector_store, 'create_summary_vector_store',
                        lambda ds_id: _get_vector_store_instance(ds_id, "summary_index_"))


@pytest.fixture(autouse=True)
def embedding_model(monkeypatch: pytest.MonkeyPatch) -> BaseEmbedding:
    model = DummyEmbeddingModel()

    # Requires that the app usages import the file and not the function directly as python creates a copy when importing the function
    monkeypatch.setattr(models, 'get_embedding_model', lambda: model)
    return model


@pytest.fixture(autouse=True)
def llm(monkeypatch: pytest.MonkeyPatch) -> LLM:
    model = DummyLlm()

    # Requires that the app usages import the file and not the function directly as python creates a copy when importing the function
    monkeypatch.setattr(models, 'get_llm', lambda model_name: model)
    return model


@pytest.fixture
def s3_object(
        s3: "s3.ServiceResource", aws_region: str, document_id: str
) -> "s3.Object":
    """Put and return a mocked S3 object"""
    bucket_name = "test_bucket"
    key = "test/" + document_id

    bucket = s3.Bucket(bucket_name)
    bucket.create(CreateBucketConfiguration={"LocationConstraint": aws_region})
    return bucket.put_object(
        Key=key,
        # TODO: fixturize file
        Body=b"Some text to be summarized and indexed",
        Metadata={"originalfilename": "test.txt"},
    )


@pytest.fixture
def client(
        s3: "s3.ServiceResource",
) -> Iterator[TestClient]:
    """Return a test client for making calls to the service.

    https://www.starlette.io/testclient/

    """
    with TestClient(app) as test_client:
        yield test_client
