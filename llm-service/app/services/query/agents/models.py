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
from crewai import LLM as CrewAILLM
from llama_index.core.llms import LLM as LlamaIndexLLM

from app import config
from app.services.caii.utils import get_caii_access_token
from app.services.models.providers import (
    AzureModelProvider,
    CAIIModelProvider,
    BedrockModelProvider,
    OpenAiModelProvider,
)


def get_crewai_llm_object_direct(
    language_model: LlamaIndexLLM, model_name: str
) -> CrewAILLM:
    if AzureModelProvider.is_enabled():
        return CrewAILLM(
            model="azure/" + model_name,
            api_key=config.settings.azure_openai_api_key,
            base_url=config.settings.azure_openai_endpoint,
            api_version=config.settings.azure_openai_api_version,
        )
    elif CAIIModelProvider.is_enabled():
        if hasattr(language_model, "api_base"):
            return CrewAILLM(
                model="openai/" + model_name,
                api_key=get_caii_access_token(),
                base_url=language_model.api_base,
            )
        else:
            raise ValueError("Model type is not supported.")
    elif BedrockModelProvider.is_enabled():
        return CrewAILLM(
            model="bedrock/" + model_name,
        )
    elif OpenAiModelProvider.is_enabled():
        return CrewAILLM(
            model="openai/" + model_name,
            api_key=config.settings.openai_api_key,
            base_url=config.settings.openai_api_base,
        )
    else:
        raise ValueError("Model type is not supported.")
