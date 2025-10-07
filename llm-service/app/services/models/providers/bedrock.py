#
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
import concurrent.futures
import logging
from typing import Optional, cast, Any, Literal
from urllib.parse import unquote

import boto3
from botocore.config import Config
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from fastapi import HTTPException
from llama_index.embeddings.bedrock import BedrockEmbedding
from llama_index.llms.bedrock_converse import BedrockConverse
from llama_index.llms.bedrock_converse.utils import BEDROCK_MODELS
from llama_index.postprocessor.bedrock_rerank import AWSBedrockRerank
from pydantic import TypeAdapter

from app.config import settings, ModelSource
from ._model_provider import _ModelProvider
from ...caii.types import ModelResponse
from ...llama_utils import completion_to_prompt, messages_to_prompt
from ...utils import raise_for_http_error, timed_lru_cache

logger = logging.getLogger(__name__)

DEFAULT_BEDROCK_LLM_MODEL = "meta.llama3-1-8b-instruct-v1:0"
DEFAULT_BEDROCK_RERANK_MODEL = "cohere.rerank-v3-5:0"

BedrockModality = Literal["TEXT", "IMAGE", "EMBEDDING"]

BEDROCK_TOOL_CALLING_MODELS = {
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-7-sonnet-20250219-v1:0",
    "anthropic.claude-sonnet-4-20250514-v1:0",
}


class BedrockModelProvider(_ModelProvider):
    @staticmethod
    def get_env_var_names() -> set[str]:
        return {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"}

    @staticmethod
    def get_model_source() -> ModelSource:
        return ModelSource.BEDROCK

    @staticmethod
    def get_priority() -> int:
        return 3

    @staticmethod
    def _get_boto3_config() -> Config:
        """Get boto3 config with increased connection pool size."""
        return Config(
            max_pool_connections=30,
            retries={"max_attempts": 3, "mode": "adaptive"},
        )

    @staticmethod
    def get_foundation_models(
        modality: Optional[BedrockModality] = None,
    ) -> list[dict[str, Any]]:
        bedrock_client = boto3.client(
            "bedrock",
            region_name=settings.aws_default_region,
        )
        foundation_models = cast(
            list[dict[str, Any]],
            bedrock_client.list_foundation_models(byOutputModality=modality)[
                "modelSummaries"
            ],
        )
        return foundation_models

    @staticmethod
    def list_all_models(
        modality: Optional[BedrockModality] = None,
    ) -> list[dict[str, Any]]:
        foundation_models = BedrockModelProvider.get_foundation_models(modality)
        valid_foundation_models = []

        # Filter models based on inference types supported
        for model in foundation_models:
            if (
                "INFERENCE_PROFILE" in model["inferenceTypesSupported"]
                or "ON_DEMAND" in model["inferenceTypesSupported"]
            ):
                valid_foundation_models.append(model)

        # Order model according to provider in the given order - 1. Meta, 2. Anthropic, 3. Cohere, 4. Mistral, rest of the providers
        provider_order = ["meta", "anthropic", "cohere", "mistral ai"]

        def provider_sort_key(foundation_model: dict[str, Any]) -> tuple[int, str]:
            provider = foundation_model.get("providerName", "").lower()
            try:
                # Providers in the list get their index as sort key
                return provider_order.index(provider), ""
            except ValueError:
                # Others get a large index and are sorted alphabetically after
                return len(provider_order), provider

        valid_foundation_models.sort(key=provider_sort_key)

        return valid_foundation_models

    @staticmethod
    @timed_lru_cache(maxsize=128, seconds=300)
    def list_available_models(
        modality: Optional[BedrockModality] = None,
    ) -> list[dict[str, Any]]:
        if settings.aws_default_region is None:
            raise ValueError("AWS default region is not set")
        credentials = boto3.Session().get_credentials()
        if credentials is None:
            raise ValueError("AWS credentials not set")
        credentials = credentials.get_frozen_credentials()
        base_url = (
            f"https://bedrock.{settings.aws_default_region}.amazonaws.com/"
            "foundation-model-availability/"
        )
        models = BedrockModelProvider.list_all_models(modality)
        available_models = []
        aws_requests = []
        for model in models:
            model_id = model["modelId"]
            url = unquote(f"{base_url}{model_id}")
            request = AWSRequest(method="GET", url=url, headers={})

            # Sign the request
            SigV4Auth(credentials, "bedrock", settings.aws_default_region).add_auth(
                request
            )

            aws_requests.append((url, dict(request.headers)))

        def get_aws_responses(
            unquoted_url: str, headers: dict[str, str]
        ) -> dict[str, Any]:
            """Fetch responses from AWS for the given requests."""
            response = requests.get(unquoted_url, headers=headers)
            raise_for_http_error(response)
            return cast(dict[str, Any], response.json())

        responses: list[dict[str, Any] | None] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(
                lambda url_and_headers: get_aws_responses(*url_and_headers),
                aws_requests,
            )
            while True:
                try:
                    result = next(results)
                    responses.append(result)
                except StopIteration:
                    break
                except HTTPException as e:
                    model_id = str(e).split("/")[-1]
                    logger.exception(
                        "Error fetching data for model %s",
                        model_id,
                    )
                    responses.append(None)
                    continue
                except Exception as e:
                    logger.exception(
                        "Unexpected error fetching data: %s",
                        e,
                    )
                    responses.append(None)
                    continue
        for model, model_data in zip(models, responses):
            if model_data:
                if model_data["entitlementAvailability"] == "AVAILABLE":
                    available_models.append(model)

        return available_models

    @staticmethod
    def list_llm_models() -> list[ModelResponse]:
        modality: BedrockModality = TypeAdapter(BedrockModality).validate_python("TEXT")
        available_models = BedrockModelProvider.list_available_models(modality)

        model_arns = BedrockModelProvider._get_model_arns()

        models = []
        for model in available_models:
            # Skip models that are not in the Llama-index BEDROCK_MODELS mapping
            if BEDROCK_MODELS.get(model["modelId"]) is None:
                continue
            if "rerank" not in model["modelId"].lower():
                if "ON_DEMAND" in model["inferenceTypesSupported"]:
                    models.append(
                        ModelResponse(
                            model_id=model["modelId"],
                            name=model["modelName"],
                            available=True,
                            tool_calling_supported=BedrockModelProvider._is_tool_calling_supported(
                                model
                            ),
                        )
                    )
                else:
                    arn_model_response = (
                        BedrockModelProvider._get_model_arn_by_profiles(
                            model["modelId"], model_arns
                        )
                    )
                    if arn_model_response:
                        arn_model_response.tool_calling_supported = (
                            BedrockModelProvider._is_tool_calling_supported(model)
                        )
                        models.append(arn_model_response)

        return models

    @staticmethod
    def _is_tool_calling_supported(model: dict[str, Any]) -> bool:
        return True if model["modelId"] in BEDROCK_TOOL_CALLING_MODELS else False

    @staticmethod
    def _get_model_arn_by_profiles(
        suffix: str,
        profiles: list[dict[str, str]],
    ) -> Optional[ModelResponse]:
        for profile in profiles:
            if profile["inferenceProfileId"].endswith(suffix):
                return ModelResponse(
                    model_id=profile["inferenceProfileId"],
                    name=profile["inferenceProfileName"],
                    available=True,
                )
        return None

    @staticmethod
    def _get_model_arns() -> list[dict[str, str]]:
        bedrock_client = boto3.client(
            "bedrock",
            region_name=settings.aws_default_region,
        )
        profiles = bedrock_client.list_inference_profiles()["inferenceProfileSummaries"]
        return cast(list[dict[str, str]], profiles)

    @staticmethod
    def list_embedding_models() -> list[ModelResponse]:
        modality: BedrockModality = TypeAdapter(BedrockModality).validate_python(
            "EMBEDDING"
        )
        available_models = BedrockModelProvider.list_available_models(modality)

        models = []
        for model in available_models:
            models.append(
                ModelResponse(
                    model_id=model["modelId"], name=model["modelName"], available=True
                )
            )

        return models

    @staticmethod
    def list_reranking_models() -> list[ModelResponse]:
        return [
            ModelResponse(
                model_id=DEFAULT_BEDROCK_RERANK_MODEL,
                name="Cohere Rerank v3.5",
            ),
            ModelResponse(
                model_id="amazon.rerank-v1:0",
                name="Amazon Rerank v1",
            ),
        ]

    @staticmethod
    def get_llm_model(name: str) -> BedrockConverse:
        return BedrockConverse(
            model=name,
            messages_to_prompt=messages_to_prompt,
            completion_to_prompt=completion_to_prompt,
            max_tokens=2048,
        )

    @staticmethod
    def get_embedding_model(name: str) -> BedrockEmbedding:
        return BedrockEmbedding(
            model_name=name,
            botocore_config=BedrockModelProvider._get_boto3_config(),
        )

    @staticmethod
    def get_reranking_model(name: str, top_n: int) -> AWSBedrockRerank:
        return AWSBedrockRerank(rerank_model_name=name, top_n=top_n)


# ensure interface is implemented
_ = BedrockModelProvider()
