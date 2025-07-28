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

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor

from ._model_provider import ModelProvider
from ...caii.caii import (
    get_caii_llm_models,
    get_caii_embedding_models,
    get_caii_reranking_models,
    get_llm as get_caii_llm_model,
    get_embedding_model as get_caii_embedding_model,
    get_reranking_model as get_caii_reranking_model,
    describe_endpoint,
)
from ...caii.types import ModelResponse
from ...llama_utils import completion_to_prompt, messages_to_prompt
from ...utils import timed_lru_cache


class CAIIModelProvider(ModelProvider):
    @staticmethod
    def get_env_var_names() -> set[str]:
        return {"CAII_DOMAIN"}

    @staticmethod
    @timed_lru_cache(maxsize=1, seconds=300)
    def list_llm_models() -> list[ModelResponse]:
        return get_caii_llm_models()

    @staticmethod
    @timed_lru_cache(maxsize=1, seconds=300)
    def list_embedding_models() -> list[ModelResponse]:
        return get_caii_embedding_models()

    @staticmethod
    @timed_lru_cache(maxsize=1, seconds=300)
    def list_reranking_models() -> list[ModelResponse]:
        return get_caii_reranking_models()

    @staticmethod
    @timed_lru_cache(maxsize=32, seconds=300)
    def get_llm_model(name: str) -> LLM:
        endpoint = describe_endpoint(endpoint_name=name)
        return get_caii_llm_model(
            endpoint=endpoint,
            messages_to_prompt=messages_to_prompt,
            completion_to_prompt=completion_to_prompt,
        )

    @staticmethod
    @timed_lru_cache(maxsize=32, seconds=300)
    def get_embedding_model(name: str) -> BaseEmbedding:
        return get_caii_embedding_model(model_name=name)

    @staticmethod
    @timed_lru_cache(maxsize=32, seconds=300)
    def get_reranking_model(name: str, top_n: int) -> BaseNodePostprocessor:
        return get_caii_reranking_model(name, top_n)


# ensure interface is implemented
_ = CAIIModelProvider()
