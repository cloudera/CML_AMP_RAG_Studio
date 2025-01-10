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
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, cast

import lipsum
import pytest
import qdrant_client as q_client
from fastapi.testclient import TestClient
from llama_index.core.base.embeddings.base import BaseEmbedding, Embedding
from llama_index.core.llms import LLM

from app.ai.vector_stores.qdrant import QdrantVectorStore
from app.main import app
from app.services import data_sources_metadata_api, models
from app.services.data_sources_metadata_api import RagDataSource
from app.services.noop_models import DummyLlm


@dataclass
class BotoObject:
    bucket_name: str
    key: str


@pytest.fixture
def qdrant_client() -> q_client.QdrantClient:
    return q_client.QdrantClient(":memory:")


@pytest.fixture(autouse=True)
def databases_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> str:
    databases_dir: str = str(tmp_path / "databases")
    monkeypatch.setenv("RAG_DATABASES_DIR", databases_dir)
    os.makedirs(databases_dir, exist_ok=True)
    return databases_dir


@pytest.fixture(autouse=True)
def use_local_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("S3_RAG_DOCUMENT_BUCKET", "")


@pytest.fixture
def document_id(index_document_request_body: dict[str, Any]) -> str:
    return cast(str, index_document_request_body["s3_document_key"].split("/")[-1])


@pytest.fixture
def data_source_id() -> int:
    return -1


@pytest.fixture
def index_document_request_body(
    data_source_id: int, s3_object: BotoObject
) -> Dict[str, Any]:
    return {
        "data_source_id": data_source_id,
        "s3_bucket_name": s3_object.bucket_name,
        "s3_document_key": s3_object.key,
        "original_filename": "test.txt",
        "configuration": {
            "chunk_size": 512,
            "chunk_overlap": 10,
        },
    }


class DummyEmbeddingModel(BaseEmbedding):
    def _get_query_embedding(self, query: str) -> Embedding:
        return [0.1] * 1024

    async def _aget_query_embedding(self, query: str) -> Embedding:
        return [0.1] * 1024

    def _get_text_embedding(self, text: str) -> Embedding:
        return [0.1] * 1024


@pytest.fixture(autouse=True)
def vector_store(
    monkeypatch: pytest.MonkeyPatch, qdrant_client: q_client.QdrantClient
) -> None:
    original = QdrantVectorStore.for_chunks
    monkeypatch.setattr(
        QdrantVectorStore,
        "for_chunks",
        lambda ds_id: original(ds_id, qdrant_client),
    )


@pytest.fixture(autouse=True)
def summary_vector_store(
    monkeypatch: pytest.MonkeyPatch, qdrant_client: q_client.QdrantClient
) -> None:
    original = QdrantVectorStore.for_summaries
    monkeypatch.setattr(
        QdrantVectorStore,
        "for_summaries",
        lambda data_source_id: original(data_source_id, qdrant_client),
    )


@pytest.fixture(autouse=True)
def datasource_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    def get_datasource_metadata(data_source_id: int) -> RagDataSource:
        return RagDataSource(
            id=data_source_id,
            name="test",
            embedding_model="test",
            summarization_model="test",
            chunk_size=512,
            chunk_overlap_percent=10,
            time_created=datetime.now(),
            time_updated=datetime.now(),
            created_by_id="test",
            updated_by_id="test",
            connection_type="test",
            document_count=1,
            total_doc_size=1,
        )

    monkeypatch.setattr(
        data_sources_metadata_api, "get_metadata", get_datasource_metadata
    )


@pytest.fixture(autouse=True)
def embedding_model(monkeypatch: pytest.MonkeyPatch) -> BaseEmbedding:
    model = DummyEmbeddingModel()

    # this is the method signature of the original, even we're not using the model name
    def get_embedding_model(model_name: str = "dummy_value") -> BaseEmbedding:
        return model

    # Requires that the app usages import the file and not the function directly as python creates a copy when importing the function
    monkeypatch.setattr(models, "get_embedding_model", get_embedding_model)
    monkeypatch.setattr(models, "get_noop_embedding_model", get_embedding_model)
    return model


@pytest.fixture(autouse=True)
def llm(monkeypatch: pytest.MonkeyPatch) -> LLM:
    model = DummyLlm()

    def get_llm(model_name: str = "dummy_value") -> LLM:
        return model

    # Requires that the app usages import the file and not the function directly as python creates a copy when importing the function
    monkeypatch.setattr(models, "get_llm", get_llm)
    return model


@pytest.fixture
def test_file(databases_dir: str, s3_object: BotoObject) -> pathlib.Path:
    body = lipsum.generate_words(1000)
    target_path = f"{databases_dir}/file_storage/{s3_object.key}"
    path = pathlib.Path(target_path)
    os.makedirs(path.parent, exist_ok=True)
    with open(target_path, "w") as f:
        f.write(body)
    return path


@pytest.fixture
def s3_object() -> BotoObject:
    """Return a mocked S3 object"""
    bucket_name = "test_bucket"
    key = "test/" + str(uuid.uuid4())
    return BotoObject(bucket_name=bucket_name, key=key)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Return a test client for making calls to the service.

    https://www.starlette.io/testclient/

    """
    with TestClient(app) as test_client:
        yield test_client
