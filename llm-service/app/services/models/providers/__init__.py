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
from app.config import settings
from .azure import AzureModelProvider
from .bedrock import BedrockModelProvider
from .caii import CAIIModelProvider
from .openai import OpenAiModelProvider
from ._model_provider import ModelProvider

__all__ = [
    "AzureModelProvider",
    "BedrockModelProvider",
    "CAIIModelProvider",
    "OpenAiModelProvider",
    "get_provider_class",
]


def get_provider_class() -> type[ModelProvider]:
    """Return the ModelProvider subclass for the given provider name."""
    model_provider = settings.model_provider
    if model_provider == "Azure":
        return AzureModelProvider
    elif model_provider == "CAII":
        return CAIIModelProvider
    elif model_provider == "OpenAI":
        return OpenAiModelProvider
    elif model_provider == "Bedrock":
        return BedrockModelProvider

    # Fallback to priority order if no specific provider is set
    if AzureModelProvider.is_enabled():
        return AzureModelProvider
    elif OpenAiModelProvider.is_enabled():
        return OpenAiModelProvider
    elif BedrockModelProvider.is_enabled():
        return BedrockModelProvider
    return CAIIModelProvider
