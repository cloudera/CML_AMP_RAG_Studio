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
import io
import json
import random
from contextlib import AbstractContextManager
from typing import Iterator, Callable, Any
from unittest.mock import patch
from urllib.parse import urljoin

import botocore
import pytest
import responses
from fastapi.testclient import TestClient
from llama_index.llms.bedrock_converse.utils import BEDROCK_MODELS

from app.config import settings
from app.services.caii.types import ModelResponse
from app.services.models.providers import BedrockModelProvider
from .testing_chat_history_manager import (
    patch_get_chat_history_manager,
)
from .utils import patch_env_vars

TEXT_MODELS = [
    ("amazon.unavailable-text-model-v1", "NOT_AVAILABLE"),
    ("amazon.available-text-model-v1", "AVAILABLE"),
]
EMBEDDING_MODELS = [
    ("amazon.unavailable-embedding-model-v1", "NOT_AVAILABLE"),
    ("amazon.available-embedding-model-v1", "AVAILABLE"),
]
RERANKING_MODELS = [
    ("amazon.available-reranking-model-v1", "AVAILABLE"),
]


def _patch_requests() -> AbstractContextManager[responses.RequestsMock]:
    bedrock_url_base = f"https://bedrock.{settings.aws_default_region}.amazonaws.com/"
    r_mock = responses.RequestsMock(assert_all_requests_are_fired=False)
    for model_id, availability in TEXT_MODELS + EMBEDDING_MODELS:
        r_mock.get(
            urljoin(
                bedrock_url_base,
                f"foundation-model-availability/{model_id}",
            ),
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

    return r_mock


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
                "TEXT": TEXT_MODELS,
                "EMBEDDING": EMBEDDING_MODELS,
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
                    for model_id, _ in TEXT_MODELS + EMBEDDING_MODELS
                ],
            }
        elif operation_name == "InvokeModel":
            texts: list[str] = json.loads(api_params["body"])["inputText"]
            return {
                "contentType": "application/json",
                # TODO: does this need to be botocore.response.StreamingBody?
                "body": io.BytesIO(
                    json.dumps(
                        {
                            "texts": texts,
                            "embeddings": [
                                [random.gauss(mu=0.0, sigma=0.1) for _ in range(16)]
                                for _ in texts
                            ],
                        }
                    ).encode()
                ),
            }
        elif operation_name == "Converse":
            return {
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "\n\nTest response."}],
                    }
                },
                "stopReason": "end_turn",
                # "usage": {"inputTokens": 21, "outputTokens": 75, "totalTokens": 96},
                # "metrics": {"latencyMs": 827},
            }
        elif operation_name == "Rerank":
            return {
                "results": [
                    # TODO: Is the document store checked prior to this? Do I need to mock that too?
                    {"index": 0, "relevanceScore": random.random()},
                    {"index": 1, "relevanceScore": random.random()},
                    {"index": 2, "relevanceScore": random.random()},
                ]
            }
        else:
            # passthrough
            return make_api_call(self, operation_name, api_params)

    return patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call)


@pytest.fixture(autouse=True)
def mock_bedrock(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    with patch_env_vars(BedrockModelProvider):
        with (
            _patch_requests(),
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


# TODO: move test functions to a discoverable place
def test_bedrock_models(client: TestClient) -> None:
    response = client.get("/llm-service/models/model_source")
    assert response.status_code == 200
    assert response.json() == "Bedrock"

    available_embedding_models = [
        model_id
        for model_id, availability in EMBEDDING_MODELS
        if availability == "AVAILABLE"
    ]
    response = client.get("/llm-service/models/embeddings")
    assert response.status_code == 200
    assert [
        model["model_id"] for model in response.json()
    ] == available_embedding_models
    # for model_id in available_embedding_models:
    #     response = client.get(f"/llm-service/models/embedding/{model_id}/test")
    #     assert response.status_code == 200  # TODO

    available_text_models = [
        model_id
        for model_id, availability in TEXT_MODELS
        if availability == "AVAILABLE"
    ]
    response = client.get("/llm-service/models/llm")
    assert response.status_code == 200
    assert [model["model_id"] for model in response.json()] == available_text_models
    for model_id in available_text_models:
        response = client.get(f"/llm-service/models/llm/{model_id}/test")
        assert response.status_code == 200

    available_reranking_models = [
        model_id
        for model_id, availability in RERANKING_MODELS
        if availability == "AVAILABLE"
    ]
    response = client.get("/llm-service/models/reranking")
    assert response.status_code == 200
    assert [
        model["model_id"] for model in response.json()
    ] == available_reranking_models
    # for model_id in available_reranking_models:
    #     response = client.get(f"/llm-service/models/reranking/{model_id}/test")
    #     assert response.status_code == 200  # TODO


def test_bedrock_sessions(client: TestClient) -> None:
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

    # response = client.post("/llm-service/sessions/1/rename-session")
    # assert response.status_code == 200


# def test_bedrock_chat(client: TestClient) -> None:
#     response = client.post("/llm-service/sessions/suggest-questions")
#     print(f"{response.json()=}")
#     assert response.status_code == 200
#
#     response = client.post("/llm-service/sessions/1/stream-completion")
#     assert response.status_code == 200
