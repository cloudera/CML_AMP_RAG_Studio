import time
start_time = time.time()
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
from typing import List, Optional, cast

import boto3

from app.config import settings
from ...caii.types import ModelResponse
from ._model_provider import ModelProvider

DEFAULT_BEDROCK_LLM_MODEL = "meta.llama3-1-8b-instruct-v1:0"
DEFAULT_BEDROCK_RERANK_MODEL = "cohere.rerank-v3-5:0"


class BedrockModelProvider(ModelProvider):
    @staticmethod
    def get_env_var_names() -> set[str]:
        return {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"}

    @staticmethod
    def get_llm_models() -> List[ModelResponse]:
        models = [
            ModelResponse(
                model_id=DEFAULT_BEDROCK_LLM_MODEL, name="Llama3.1 8B Instruct v1"
            ),
            ModelResponse(
                model_id="meta.llama3-1-70b-instruct-v1:0",
                name="Llama3.1 70B Instruct v1",
            ),
            ModelResponse(
                model_id="cohere.command-r-plus-v1:0", name="Cohere Command R Plus v1"
            ),
        ]

        model_arns = BedrockModelProvider._get_model_arns()

        claude37sonnet = BedrockModelProvider._get_model_arn_by_profiles(
            "anthropic.claude-3-7-sonnet-20250219-v1:0", model_arns
        )
        if claude37sonnet:
            models.append(claude37sonnet)

        llama323b = BedrockModelProvider._get_model_arn_by_profiles(
            "meta.llama3-2-3b-instruct-v1:0", model_arns
        )
        if llama323b:
            models.append(llama323b)

        llama321b = BedrockModelProvider._get_model_arn_by_profiles(
            "meta.llama3-2-1b-instruct-v1:0", model_arns
        )
        if llama321b:
            models.append(llama321b)

        return models

    @staticmethod
    def _get_model_arn_by_profiles(
        suffix: str, profiles: List[dict[str, str]]
    ) -> Optional[ModelResponse]:
        for profile in profiles:
            if profile["inferenceProfileId"].endswith(suffix):
                return ModelResponse(
                    model_id=profile["inferenceProfileId"],
                    name=profile["inferenceProfileName"],
                )
        return None

    @staticmethod
    def _get_model_arns() -> List[dict[str, str]]:
        bedrock_client = boto3.client("bedrock", region_name=settings.aws_default_region)
        profiles = bedrock_client.list_inference_profiles()["inferenceProfileSummaries"]
        return cast(List[dict[str, str]], profiles)

    @staticmethod
    def get_embedding_models() -> List[ModelResponse]:
        return [
            ModelResponse(
                model_id="cohere.embed-english-v3",
                name="Cohere Embed English v3",
            ),
            ModelResponse(
                model_id="cohere.embed-multilingual-v3",
                name="Cohere Embed Multilingual v3",
            ),
        ]

    @staticmethod
    def get_reranking_models() -> List[ModelResponse]:
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


# ensure interface is implemented
_ = BedrockModelProvider()

print('services/models/providers/bedrock.py took {time.time() - start_time} seconds to import')
