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

from typing import List

from ...caii.types import ModelResponse
from ._model_provider import ModelProvider


class AzureModelProvider(ModelProvider):
    @staticmethod
    def get_env_var_names() -> set[str]:
        return {"AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "OPENAI_API_VERSION"}

    @staticmethod
    def get_llm_models() -> List[ModelResponse]:
        return [
            ModelResponse(
                model_id="gpt-4o",
                name="OpenAI GPT-4o",
            ),
            ModelResponse(
                model_id="gpt-4o-mini",
                name="OpenAI GPT-4o-mini",
            ),
        ]

    @staticmethod
    def get_embedding_models() -> List[ModelResponse]:
        return [
            ModelResponse(
                model_id="text-embedding-ada-002",
                name="Text Embedding Ada 002",
            ),
            ModelResponse(
                model_id="text-embedding-3-small",
                name="Text Embedding 3 Small",
            ),
        ]

    @staticmethod
    def get_reranking_models() -> List[ModelResponse]:
        return []


# ensure interface is implemented
_ = AzureModelProvider()

print('services/models/providers/azure.py took {time.time() - start_time} seconds to import')
