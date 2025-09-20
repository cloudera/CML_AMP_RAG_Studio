#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2025
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
#  Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
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
#
import contextlib
import dataclasses
import io
import itertools
import json
import random
import re
import string
from contextlib import AbstractContextManager
from typing import Iterator, Callable, Any, cast
from unittest.mock import patch
from urllib.parse import urljoin

import botocore
import pytest
import responses
from fastapi.testclient import TestClient
from llama_index.llms.bedrock_converse.utils import BEDROCK_MODELS

from app.config import settings
from app.routers.index.sessions import RagStudioChatRequest
from app.services.caii.types import ModelResponse
from app.services.metadata_apis import session_metadata_api
from app.services.metadata_apis.session_metadata_api import (
    Session,
    SessionQueryConfiguration,
)
from app.services.models import Reranking
from app.services.models.providers import BedrockModelProvider
from .testing_chat_history_manager import (
    patch_get_chat_history_manager,
)
from .utils import patch_env_vars

EMBEDDING_MODELS = [
    ("amazon.unavailable-embedding-model-v1", "NOT_AVAILABLE"),
    ("amazon.available-embedding-model-v1", "AVAILABLE"),
]
TEXT_MODELS = [
    ("amazon.unavailable-text-model-v1", "NOT_AVAILABLE"),
    ("amazon.available-text-model-v1", "AVAILABLE"),
]
RERANKING_MODELS = [
    ("amazon.available-reranking-model-v1", "AVAILABLE"),
]

AVAILABLE_EMBEDDING_MODELS = [
    model_id
    for model_id, availability in EMBEDDING_MODELS
    if availability == "AVAILABLE"
]
AVAILABLE_TEXT_MODELS = [
    model_id for model_id, availability in TEXT_MODELS if availability == "AVAILABLE"
]
AVAILABLE_RERANKING_MODELS = [
    model_id
    for model_id, availability in RERANKING_MODELS
    if availability == "AVAILABLE"
]

MOCK_EMBEDDING_RESPONSE = [random.gauss(mu=0.0, sigma=0.1) for _ in range(16)]
MOCK_TEXT_RESPONSE = "\n\nThis is a test response."
MOCK_RERANKING_RESPONSE = [
    {"index": i, "relevanceScore": random.random()}
    for i in range(len(Reranking._TEST_NODES))
]


@pytest.fixture
def requests_mock() -> Iterator[responses.RequestsMock]:
    with responses.RequestsMock(assert_all_requests_are_fired=False) as requests_mock:
        yield requests_mock


@contextlib.contextmanager
def _patch_bedrock_requests(requests_mock: responses.RequestsMock) -> Iterator[None]:
    model_availability_url_base = urljoin(
        f"https://bedrock.{settings.aws_default_region}.amazonaws.com/",
        "foundation-model-availability/",
    )
    for model_id, availability in EMBEDDING_MODELS + TEXT_MODELS:
        requests_mock.get(
            urljoin(model_availability_url_base, model_id),
            json={
                "agreementAvailability": {
                    "errorMessage": None,
                    "status": availability,
                },
                "authorizationStatus": "AUTHORIZED",
                "entitlementAvailability": availability,
                "modelId": model_id,
                "regionAvailability": "AVAILABLE",
            },
        )

    try:
        yield
    finally:
        for model_id, _ in EMBEDDING_MODELS + TEXT_MODELS:
            requests_mock.remove(
                responses.GET,
                urljoin(model_availability_url_base, model_id),
            )


make_api_callable = Callable[[type, str, dict[str, str]], Any]


def _patch_boto3() -> AbstractContextManager[make_api_callable]:
    make_api_call: make_api_callable = botocore.client.BaseClient._make_api_call  # type: ignore

    def mock_make_api_call(
        self: type,
        operation_name: str,
        api_params: dict[str, str],
    ) -> Any:
        """Mock Boto3 Bedrock operations, since moto doesn't have full coverage.

        Based on https://docs.getmoto.org/en/latest/docs/services/patching_other_services.html.

        """
        if operation_name == "ListFoundationModels":
            modality = api_params["byOutputModality"]
            models = {
                "EMBEDDING": EMBEDDING_MODELS,
                "TEXT": TEXT_MODELS,
            }.get(modality)
            if models is None:
                raise ValueError(f"test encountered unexpected modality {modality}")

            return {
                "modelSummaries": [
                    {
                        "modelArn": f"arn:aws:bedrock:{settings.aws_default_region}::foundation-model/{model_id}",
                        "modelId": model_id,
                        "modelName": model_id.upper(),
                        "providerName": "Test",
                        "inputModalities": ["TEXT"],
                        "outputModalities": [modality],
                        "responseStreamingSupported": modality == "TEXT",  # arbitrary
                        "customizationsSupported": [],
                        "inferenceTypesSupported": ["ON_DEMAND"],
                        "modelLifecycle": {"status": "ACTIVE"},
                    }
                    for model_id, _ in models
                ],
            }
        elif operation_name == "ListInferenceProfiles":
            return {
                "inferenceProfileSummaries": [
                    {
                        "inferenceProfileName": f"US {model_id.upper()}",
                        "description": f"Routes requests to {model_id.upper()} in {settings.aws_default_region}.",
                        "inferenceProfileArn": f"arn:aws:bedrock:{settings.aws_default_region}:123456789012:inference-profile/{model_id}",
                        "models": [
                            {
                                "modelArn": f"arn:aws:bedrock:{settings.aws_default_region}::foundation-model/{model_id}"
                            },
                        ],
                        "inferenceProfileId": model_id,
                        "status": "ACTIVE",
                        "type": "SYSTEM_DEFINED",
                    }
                    for model_id, _ in EMBEDDING_MODELS + TEXT_MODELS
                ],
            }
        elif operation_name == "InvokeModel":
            return {
                "body": io.BytesIO(
                    json.dumps({"embedding": MOCK_EMBEDDING_RESPONSE}).encode(),
                ),
            }
        elif operation_name == "Converse":
            return {
                "ResponseMetadata": {
                    "HTTPHeaders": {"content-type": "application/json"},
                },
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": MOCK_TEXT_RESPONSE}],
                    }
                },
                "stopReason": "end_turn",
            }
        elif operation_name == "ConverseStream":
            leading_whitespace, text_response, ending_punctuation = re.match(
                rf"^(\s+)([\w ]+)([{re.escape(string.punctuation)}])$",
                MOCK_TEXT_RESPONSE,
            ).groups()  # type: ignore[union-attr]
            response = iter(text_response.split(" "))
            return {
                "ResponseMetadata": {
                    "HTTPHeaders": {
                        "content-type": "application/vnd.amazon.eventstream",
                    },
                },
                "stream": itertools.chain(
                    [
                        {"messageStart": {"role": "assistant"}},
                        {
                            "contentBlockDelta": {
                                "delta": {"text": leading_whitespace},
                                "contentBlockIndex": 0,
                            }
                        },
                        {
                            "contentBlockDelta": {
                                "delta": {"text": next(response)},
                                "contentBlockIndex": 0,
                            }
                        },
                    ],
                    (
                        {
                            "contentBlockDelta": {
                                "delta": {"text": " " + delta},
                                "contentBlockIndex": 0,
                            }
                        }
                        for delta in response
                    ),
                    [
                        {
                            "contentBlockDelta": {
                                "delta": {"text": ending_punctuation},
                                "contentBlockIndex": 0,
                            }
                        },
                        {
                            "contentBlockDelta": {
                                "delta": {"text": ""},
                                "contentBlockIndex": 0,
                            }
                        },
                        {"contentBlockStop": {"contentBlockIndex": 0}},
                        {"messageStop": {"stopReason": "end_turn"}},
                    ],
                ),
            }
        elif operation_name == "Rerank":
            return {"results": MOCK_RERANKING_RESPONSE}
        else:
            # passthrough
            return make_api_call(self, operation_name, api_params)

    return cast(
        AbstractContextManager[make_api_callable],
        patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call),
    )


@pytest.fixture()
def mock_bedrock(
    monkeypatch: pytest.MonkeyPatch,
    requests_mock: responses.RequestsMock,
) -> Iterator[None]:
    with patch_env_vars(BedrockModelProvider):
        with (
            _patch_bedrock_requests(requests_mock),
            _patch_boto3(),
            patch(  # mock reranking models, which are hard-coded in our app
                "app.services.models.providers.BedrockModelProvider.list_reranking_models",
                new=lambda: [
                    ModelResponse(model_id=model_id, name=model_id.upper())
                    for model_id, _ in RERANKING_MODELS
                ],
            ),
            patch(  # work around a llama-index filter we have in list_llm_models()
                "app.services.models.providers.bedrock.BEDROCK_MODELS",
                new=BEDROCK_MODELS | {model_id: 128000 for model_id, _ in TEXT_MODELS},
            ),
        ):
            yield


@dataclasses.dataclass
class MockJavaResponses:
    get_session: responses.BaseResponse


@pytest.fixture()
def mock_java(
    request: pytest.FixtureRequest,
    requests_mock: responses.RequestsMock,
) -> Iterator[MockJavaResponses]:
    session_base = Session(  # TODO
        id=1,
        name="Greetings",
        data_source_ids=[],
        project_id=1,
        inference_model="meta.llama3-8b-instruct-v1:0",  # TODO: grab from model provider?
        associated_data_source_id=2,
        rerank_model=None,
        response_chunks=10,
        query_configuration=SessionQueryConfiguration(
            enable_hyde=False,
            enable_summary_filter=True,
            enable_tool_calling=False,
            disable_streaming=False,  # TODO: make this configurable by tests
            selected_tools=[],
        ),
    )
    session_modifications = getattr(request, "param", dict()).copy()
    session_base.query_configuration = session_base.query_configuration.model_copy(
        update=session_modifications.pop("query_configuration", dict()),
    )
    SessionQueryConfiguration.model_validate(session_base.query_configuration)
    session = session_base.model_copy(update=session_modifications)
    Session.model_validate(session)

    session_metadata_url_base = re.escape(
        session_metadata_api.url_template().format(""),
    )
    session_metadata_url_pattern = re.compile(session_metadata_url_base + r"\d+")
    get_session_response = requests_mock.get(
        session_metadata_url_pattern,
        json=session.model_dump(by_alias=True),
    )

    try:
        yield MockJavaResponses(
            get_session=get_session_response,
        )
    finally:
        requests_mock.remove(responses.GET, session_metadata_url_pattern)
        requests_mock.remove(responses.POST, session_metadata_url_pattern)


# TODO: move test functions to a discoverable place
@pytest.mark.usefixtures("mock_bedrock")
class TestBedrock:
    def test_model_source(self, client: TestClient) -> None:
        response = client.get("/llm-service/models/model_source")
        assert response.status_code == 200
        assert response.json() == "Bedrock"

    def test_get_models(self, client: TestClient) -> None:
        response = client.get("/llm-service/models/embeddings")
        assert response.status_code == 200
        assert [
            model["model_id"] for model in response.json()
        ] == AVAILABLE_EMBEDDING_MODELS

        response = client.get("/llm-service/models/llm")
        assert response.status_code == 200
        assert [model["model_id"] for model in response.json()] == AVAILABLE_TEXT_MODELS

        response = client.get("/llm-service/models/reranking")
        assert response.status_code == 200
        assert [
            model["model_id"] for model in response.json()
        ] == AVAILABLE_RERANKING_MODELS

    def test_test_models(self, client: TestClient) -> None:
        for model_id in AVAILABLE_EMBEDDING_MODELS:
            response = client.get(f"/llm-service/models/embedding/{model_id}/test")
            assert response.status_code == 200

        for model_id in AVAILABLE_TEXT_MODELS:
            response = client.get(f"/llm-service/models/llm/{model_id}/test")
            assert response.status_code == 200

        for model_id in AVAILABLE_RERANKING_MODELS:
            response = client.get(f"/llm-service/models/reranking/{model_id}/test")
            assert response.status_code == 200

    def test_get_chat_history(self, client: TestClient) -> None:
        session_id = 1
        with patch_get_chat_history_manager() as get_testing_chat_history_manager:
            chat_history = get_testing_chat_history_manager().retrieve_chat_history(
                session_id=session_id
            )

            response = client.get(f"/llm-service/sessions/{session_id}/chat-history")
            assert response.status_code == 200
            assert response.json()["data"] == [msg.model_dump() for msg in chat_history]

            msg = chat_history[0]  # TODO: randomize?
            response = client.get(
                f"/llm-service/sessions/{msg.session_id}/chat-history/{msg.id}",
            )
            assert response.status_code == 200
            assert response.json() == msg.model_dump()

            # TODO: maybe call the chat endpoint and see if history changes

    # @pytest.mark.usefixtures("mock_java")
    # def test_session(self, client: TestClient) -> None:
    #     session_id = 1
    #     with patch_get_chat_history_manager():
    #         response = client.post(f"/llm-service/sessions/{session_id}/rename-session")
    #         print(f"{response.json()}")
    #         assert response.status_code == 200
    #
    #     response = client.post("/llm-service/sessions/suggest-questions")
    #     print(f"{response.json()=}")
    #     assert response.status_code == 200
    #
    #     # TODO: patch chat history manager?
    #     response = client.post(f"/llm-service/sessions/{session_id}/suggest-questions")
    #     print(f"{response.json()=}")
    #     assert response.status_code == 200

    @pytest.mark.parametrize(
        "mock_java",
        [{"query_configuration": {"disable_streaming": True}}],
        indirect=True,
    )
    def test_non_streaming_chat(
        self,
        client: TestClient,
        mock_java: MockJavaResponses,
    ) -> None:
        """Test ``/stream-completion`` when ``disable_streaming = True``

        Checks that the endpoint returns the correct response and appends to chat history.

        """
        session_id = 1
        with patch_get_chat_history_manager() as get_testing_chat_history_manager:
            chat_history_manager = get_testing_chat_history_manager()
            pre_chat_history = chat_history_manager.retrieve_chat_history(
                session_id=session_id,
            ).copy()

            response = client.post(
                f"/llm-service/sessions/{session_id}/stream-completion",
                json=RagStudioChatRequest(query="test question").model_dump(),
            )

            post_chat_history = chat_history_manager.retrieve_chat_history(
                session_id=session_id,
            )

        # check chat response
        assert response.status_code == 200
        response_stream: Iterator[dict[str, Any]] = map(
            lambda line: json.loads(line.removeprefix("data: ")),
            filter(None, response.iter_lines()),
        )
        assert (
            next(response_stream)["event"].items()
            >= {
                "type": "thinking",
                "name": "thinking",
                "data": "Preparing full response...",
            }.items()
        )
        assert (
            next(response_stream)["event"].items()
            >= {
                "type": "done",
                "name": "chat_done",
                "data": None,
            }.items()
        )
        response_id = next(response_stream)["response_id"]
        with pytest.raises(StopIteration):
            next(response_stream)

        # check chat history
        assert pre_chat_history[-1].id != response_id
        assert post_chat_history[-1].id == response_id

    @pytest.mark.parametrize(
        "mock_java",
        [{"query_configuration": {"disable_streaming": False}}],
        indirect=True,
    )
    def test_streaming_chat(
        self,
        client: TestClient,
        mock_java: MockJavaResponses,
    ) -> None:
        """Test ``/stream-completion`` when ``disable_streaming = False``

        Checks that the endpoint returns the correct response and appends to chat history.

        """
        session_id = 1
        with patch_get_chat_history_manager() as get_testing_chat_history_manager:
            chat_history_manager = get_testing_chat_history_manager()
            pre_chat_history = chat_history_manager.retrieve_chat_history(
                session_id=session_id,
            ).copy()

            response = client.post(
                f"/llm-service/sessions/{session_id}/stream-completion",
                json=RagStudioChatRequest(query="test question").model_dump(),
            )

            post_chat_history = chat_history_manager.retrieve_chat_history(
                session_id=session_id,
            )

        # check chat response
        assert response.status_code == 200
        response_stream: Iterator[dict[str, Any]] = map(
            lambda line: json.loads(line.removeprefix("data: ")),
            filter(None, response.iter_lines()),
        )
        assert (
            next(response_stream)["event"].items()
            >= {
                "type": "done",
                "name": "agent_done",
                "data": None,
            }.items()
        )
        chat_response = ""
        for data in response_stream:
            if (text := data.get("text")) is None:
                break
            chat_response += text
        assert chat_response == MOCK_TEXT_RESPONSE
        # noinspection PyUnboundLocalVariable
        assert (
            data["event"].items()
            >= {
                "type": "done",
                "name": "chat_done",
                "data": None,
            }.items()
        )
        response_id = next(response_stream)["response_id"]
        with pytest.raises(StopIteration):
            next(response_stream)

        # check chat history
        assert pre_chat_history[-1].id != response_id
        assert post_chat_history[-1].id == response_id
