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
import itertools
from typing import Generator
from unittest.mock import patch
from urllib.parse import urljoin

import botocore
import pytest
import responses
from llama_index.llms.bedrock_converse.utils import BEDROCK_MODELS

from app.config import settings
from app.services.caii.types import ModelResponse
from app.services.models import ModelProvider
from app.services.models.providers import BedrockModelProvider

TEXT_MODELS = [
    ("test.unavailable-text-model-v1", "NOT_AVAILABLE"),
    ("test.available-text-model-v1", "AVAILABLE"),
]
EMBEDDING_MODELS = [
    ("test.unavailable-embedding-model-v1", "NOT_AVAILABLE"),
    ("test.available-embedding-model-v1", "AVAILABLE"),
]
RERANKING_MODELS = [
    ("test.available-reranking-model-v1", "AVAILABLE"),
]


@pytest.fixture
def mock_bedrock(monkeypatch) -> Generator[None, None, None]:
    for name in BedrockModelProvider.get_env_var_names():
        monkeypatch.setenv(name, "test")
    for name in get_all_env_var_names() - BedrockModelProvider.get_env_var_names():
        monkeypatch.delenv(name, raising=False)

    # mock calls made directly through `requests`
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

    # mock calls made through `boto3`
    make_api_call = botocore.client.BaseClient._make_api_call

    def mock_make_api_call(self, operation_name: str, api_params: dict[str, str]):
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

        else:
            # passthrough
            return make_api_call(self, operation_name, api_params)

    # mock reranking models, which are hard-coded in our app
    def list_reranking_models() -> list[ModelResponse]:
        return [
            ModelResponse(model_id=model_id, name=model_id.upper())
            for model_id, _ in RERANKING_MODELS
        ]

    with (
        r_mock,
        patch(
            "botocore.client.BaseClient._make_api_call",
            new=mock_make_api_call,
        ),
        patch(
            "app.services.models.providers.BedrockModelProvider.list_reranking_models",
            new=list_reranking_models,
        ),
        patch(  # work around a llama-index filter we have in list_llm_models()
            "app.services.models.providers.bedrock.BEDROCK_MODELS",
            new=BEDROCK_MODELS | {model_id: 128000 for model_id, _ in TEXT_MODELS},
        ),
    ):
        yield


def get_all_env_var_names() -> set[str]:
    """Return the names of all the env vars required by all model providers."""
    return set(
        itertools.chain.from_iterable(
            subcls.get_env_var_names() for subcls in ModelProvider.__subclasses__()
        )
    )


# TODO: move this test function to a discoverable place
def test_bedrock(mock_bedrock, client) -> None:
    response = client.get("/llm-service/models/model_source")
    assert response.status_code == 200
    assert response.json() == "Bedrock"

    response = client.get("/llm-service/models/embeddings")
    assert response.status_code == 200
    assert [model["model_id"] for model in response.json()] == [
        model_id
        for model_id, availability in EMBEDDING_MODELS
        if availability == "AVAILABLE"
    ]

    response = client.get("/llm-service/models/llm")
    assert response.status_code == 200
    assert [model["model_id"] for model in response.json()] == [
        model_id
        for model_id, availability in TEXT_MODELS
        if availability == "AVAILABLE"
    ]

    response = client.get("/llm-service/models/reranking")
    assert response.status_code == 200
    assert [model["model_id"] for model in response.json()] == [
        model_id
        for model_id, availability in RERANKING_MODELS
        if availability == "AVAILABLE"
    ]
