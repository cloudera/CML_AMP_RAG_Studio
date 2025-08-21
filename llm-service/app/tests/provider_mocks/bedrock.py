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
from typing import Generator
from unittest.mock import patch
from urllib.parse import urljoin

import botocore
import pytest
import responses

from app.config import settings


@pytest.fixture
def mock_bedrock() -> Generator[None, None, None]:
    BEDROCK_URL_BASE = f"https://bedrock.{settings.aws_default_region}.amazonaws.com/"
    TEXT_MODELS = [
        ("test.unavailable-text-model-v1", "NOT_AVAILABLE"),
        ("test.available-text-model-v1", "AVAILABLE"),
    ]
    EMBEDDING_MODELS = [
        ("test.unavailable-embedding-model-v1", "NOT_AVAILABLE"),
        ("test.available-embedding-model-v1", "AVAILABLE"),
    ]

    r_mock = responses.RequestsMock(assert_all_requests_are_fired=False)
    for model_id, availability in TEXT_MODELS + EMBEDDING_MODELS:
        r_mock.get(
            urljoin(
                BEDROCK_URL_BASE,
                f"foundation-model-availability/{model_id}:0",
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

    make_api_call = botocore.client.BaseClient._make_api_call

    def mock_make_api_call(self, operation_name: str, api_params: dict[str, str]):
        """Mock Bedrock calls, since moto doesn't have full coverage.

        Based on https://docs.getmoto.org/en/latest/docs/services/patching_other_services.html.

        """
        if operation_name == "ListFoundationModels":
            modality = api_params["byOutputModality"]
            if modality == "TEXT":
                return {
                    "modelSummaries": [
                        {
                            "modelArn": f"arn:aws:bedrock:{settings.aws_default_region}::foundation-model/{model_id}:0",
                            "modelId": f"{model_id}:0",
                            "modelName": model_id.upper(),
                            "providerName": "Test",
                            "inputModalities": ["TEXT"],
                            "outputModalities": ["TEXT"],
                            "responseStreamingSupported": True,
                            "customizationsSupported": [],
                            "inferenceTypesSupported": ["ON_DEMAND"],
                            "modelLifecycle": {"status": "ACTIVE"},
                        }
                        for model_id, _ in TEXT_MODELS
                    ],
                }
            elif modality == "EMBEDDING":
                return {
                    "modelSummaries": [
                        {
                            "modelArn": f"arn:aws:bedrock:{settings.aws_default_region}::foundation-model/{model_id}:0",
                            "modelId": f"{model_id}:0",
                            "modelName": model_id.upper(),
                            "providerName": "Test",
                            "inputModalities": ["TEXT"],
                            "outputModalities": ["EMBEDDING"],
                            "responseStreamingSupported": False,
                            "customizationsSupported": [],
                            "inferenceTypesSupported": ["ON_DEMAND"],
                            "modelLifecycle": {"status": "ACTIVE"},
                        }
                        for model_id, _ in EMBEDDING_MODELS
                    ],
                }
            else:
                raise ValueError(f"test encountered unexpected modality {modality}")
        elif operation_name == "ListInferenceProfiles":
            return {
                "inferenceProfileSummaries": [
                    {
                        "inferenceProfileName": f"US {model_id.upper()}",
                        "description": f"Routes requests to {model_id.upper()} in {settings.aws_default_region}.",
                        "inferenceProfileArn": f"arn:aws:bedrock:{settings.aws_default_region}:123456789012:inference-profile/{model_id}:0",
                        "models": [
                            {
                                "modelArn": f"arn:aws:bedrock:{settings.aws_default_region}::foundation-model/{model_id}:0"
                            },
                        ],
                        "inferenceProfileId": f"{model_id}:0",
                        "status": "ACTIVE",
                        "type": "SYSTEM_DEFINED",
                    }
                    for model_id, _ in TEXT_MODELS + EMBEDDING_MODELS
                ],
            }

        else:
            # passthrough
            return make_api_call(self, operation_name, api_params)

    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        with r_mock:
            yield


def test_bedrock(mock_bedrock) -> None:
    from app.services.models.providers import BedrockModelProvider

    BedrockModelProvider.list_available_models()
    BedrockModelProvider._get_model_arns()
