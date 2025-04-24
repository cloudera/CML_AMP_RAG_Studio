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
from typing import Optional

from fastapi import HTTPException
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.postprocessor.bedrock_rerank import AWSBedrockRerank

from . import _model_type
from .providers import (
    AzureModelProvider,
    BedrockModelProvider,
    CAIIModelProvider,
)
from ..caii.caii import get_reranking_model as caii_reranking
from ..caii.types import ModelResponse
from ..query.simple_reranker import SimpleReranker


class Reranking(_model_type.ModelType[BaseNodePostprocessor]):
    @classmethod
    def get(
        cls,
        model_name: Optional[str] = None,
        top_n: int = 5,
    ) -> BaseNodePostprocessor:
        if not model_name:
            return SimpleReranker(top_n=top_n)
        if AzureModelProvider.is_enabled():
            return SimpleReranker(top_n=top_n)
        if CAIIModelProvider.is_enabled():
            return caii_reranking(model_name, top_n)
        return AWSBedrockRerank(rerank_model_name=model_name, top_n=top_n)

    @staticmethod
    def get_noop() -> BaseNodePostprocessor:
        raise NotImplementedError

    @staticmethod
    def list_available() -> list[ModelResponse]:
        if AzureModelProvider.is_enabled():
            return AzureModelProvider.get_reranking_models()

        if CAIIModelProvider.is_enabled():
            return CAIIModelProvider.get_reranking_models()

        return BedrockModelProvider.get_reranking_models()

    @classmethod
    def test(cls, model_name: str) -> str:
        models = cls.list_available()
        for model in models:
            if model.model_id == model_name:
                if not CAIIModelProvider.is_enabled() or model.available:
                    node = NodeWithScore(node=TextNode(text="test"), score=0.5)
                    another_test_node = NodeWithScore(
                        node=TextNode(text="another test node"), score=0.4
                    )
                    reranking_model: BaseNodePostprocessor | None = cls.get(
                        model_name=model_name
                    )
                    if reranking_model:
                        reranking_model.postprocess_nodes(
                            [node, another_test_node], None, "test"
                        )
                        return "ok"
        raise HTTPException(status_code=404, detail="Model not found")


# ensure interface is implemented
_ = Reranking()
