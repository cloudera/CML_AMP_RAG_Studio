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
import os
from enum import Enum
from typing import List, Literal, Optional

from fastapi import HTTPException
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.embeddings.bedrock import BedrockEmbedding
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.llms.bedrock_converse import BedrockConverse
from llama_index.postprocessor.bedrock_rerank import AWSBedrockRerank


from ._azure_model_provider import AzureModelProvider
from ._bedrock_model_provider import BedrockModelProvider
from ._caii_model_provider import CAIIModelProvider
from . import _noop

from ..caii.caii import get_embedding_model as caii_embedding
from ..caii.caii import get_reranking_model as caii_reranking
from ..caii.caii import get_llm as caii_llm
from ..caii.types import ModelResponse
from ..llama_utils import completion_to_prompt, messages_to_prompt
from ..query.simple_reranker import SimpleReranker


def get_noop_embedding_model() -> BaseEmbedding:
    return _noop.DummyEmbeddingModel()


def get_noop_llm_model() -> LLM:
    return _noop.DummyLlm()


def get_reranking_model(
    model_name: Optional[str] = None, top_n: int = 5
) -> BaseNodePostprocessor | None:
    if not model_name:
        return SimpleReranker(top_n=top_n)
    if AzureModelProvider.is_enabled():
        return SimpleReranker(top_n=top_n)
    if CAIIModelProvider.is_enabled():
        return caii_reranking(model_name, top_n)
    return AWSBedrockRerank(rerank_model_name=model_name, top_n=top_n)


def get_embedding_model(model_name: Optional[str] = None) -> BaseEmbedding:
    if model_name is None:
        model_name = get_available_embedding_models()[0].model_id

    if AzureModelProvider.is_enabled():
        return AzureOpenAIEmbedding(
            model_name=model_name,
            deployment_name=model_name,
            api_key=os.environ[
                "AZURE_OPENAI_API_KEY"
            ],  # AZURE_OPENAI_API_KEY does not properly map via env var otherwise OPENAI_API_KEY is also required.
        )

    if CAIIModelProvider.is_enabled():
        return caii_embedding(model_name=model_name)

    return BedrockEmbedding(model_name=model_name)


def get_llm(model_name: Optional[str] = None) -> LLM:
    if not model_name:
        model_name = get_available_llm_models()[0].model_id

    if AzureModelProvider.is_enabled():
        return AzureOpenAI(
            model=model_name,
            engine=model_name,
            messages_to_prompt=messages_to_prompt,
            completion_to_prompt=completion_to_prompt,
        )

    if CAIIModelProvider.is_enabled():
        return caii_llm(
            endpoint_name=model_name,
            messages_to_prompt=messages_to_prompt,
            completion_to_prompt=completion_to_prompt,
        )

    return BedrockConverse(
        model=model_name,
        messages_to_prompt=messages_to_prompt,
        completion_to_prompt=completion_to_prompt,
    )


def get_available_embedding_models() -> List[ModelResponse]:
    if AzureModelProvider.is_enabled():
        return AzureModelProvider.get_embedding_models()

    if CAIIModelProvider.is_enabled():
        return CAIIModelProvider.get_embedding_models()

    return BedrockModelProvider.get_embedding_models()


def get_available_llm_models() -> list[ModelResponse]:
    if AzureModelProvider.is_enabled():
        return AzureModelProvider.get_llm_models()

    if CAIIModelProvider.is_enabled():
        return CAIIModelProvider.get_llm_models()

    return BedrockModelProvider.get_llm_models()


def get_available_rerank_models() -> List[ModelResponse]:
    if AzureModelProvider.is_enabled():
        return AzureModelProvider.get_reranking_models()

    if CAIIModelProvider.is_enabled():
        return CAIIModelProvider.get_reranking_models()

    return BedrockModelProvider.get_reranking_models()


class ModelSource(str, Enum):
    BEDROCK = "Bedrock"
    CAII = "CAII"
    AZURE = "Azure"


def get_model_source() -> ModelSource:
    if CAIIModelProvider.is_enabled():
        return ModelSource.CAII
    if AzureModelProvider.is_enabled():
        return ModelSource.AZURE
    return ModelSource.BEDROCK


def test_llm_model(model_name: str) -> Literal["ok"]:
    models = get_available_llm_models()
    for model in models:
        if model.model_id == model_name:
            if not CAIIModelProvider.is_enabled() or model.available:
                get_llm(model_name).chat(
                    messages=[
                        ChatMessage(
                            role=MessageRole.USER,
                            content="Are you available to answer questions?",
                        )
                    ]
                )
                return "ok"
            else:
                raise HTTPException(status_code=503, detail="Model not ready")

    raise HTTPException(status_code=404, detail="Model not found")


def test_embedding_model(model_name: str) -> str:
    models = get_available_embedding_models()
    for model in models:
        if model.model_id == model_name:
            if not CAIIModelProvider.is_enabled() or model.available:
                get_embedding_model(model_name).get_text_embedding("test")
                return "ok"
            else:
                raise HTTPException(status_code=503, detail="Model not ready")

    raise HTTPException(status_code=404, detail="Model not found")


def test_reranking_model(model_name: str) -> str:
    models = get_available_rerank_models()
    for model in models:
        if model.model_id == model_name:
            if not CAIIModelProvider.is_enabled() or model.available:
                node = NodeWithScore(node=TextNode(text="test"), score=0.5)
                another_test_node = NodeWithScore(
                    node=TextNode(text="another test node"), score=0.4
                )
                reranking_model: BaseNodePostprocessor | None = get_reranking_model(
                    model_name=model_name
                )
                if reranking_model:
                    reranking_model.postprocess_nodes(
                        [node, another_test_node], None, "test"
                    )
                    return "ok"
    raise HTTPException(status_code=404, detail="Model not found")
