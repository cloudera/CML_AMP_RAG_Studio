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
from typing import Literal, Optional

from fastapi import HTTPException
from llama_index.core import llms
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from . import _model_type, _noop
from .providers import (
    AzureModelProvider,
    BedrockModelProvider,
    CAIIModelProvider,
)
from .providers.openai import OpenAiModelProvider
from ..caii.types import ModelResponse


class LLM(_model_type.ModelType[llms.LLM]):
    @classmethod
    def get(cls, model_name: Optional[str] = None) -> llms.LLM:
        if not model_name:
            model_name = cls.list_available()[0].model_id

        if AzureModelProvider.is_enabled():
            return AzureModelProvider.get_llm_model(model_name)
        if CAIIModelProvider.is_enabled():
            return CAIIModelProvider.get_llm_model(model_name)
        if OpenAiModelProvider.is_enabled():
            return OpenAiModelProvider.get_llm_model(model_name)
        return BedrockModelProvider.get_llm_model(model_name)

    @staticmethod
    def get_noop() -> llms.LLM:
        return _noop.DummyLlm()

    @staticmethod
    def list_available() -> list[ModelResponse]:
        if AzureModelProvider.is_enabled():
            return AzureModelProvider.list_llm_models()
        if CAIIModelProvider.is_enabled():
            return CAIIModelProvider.list_llm_models()
        if OpenAiModelProvider.is_enabled():
            return OpenAiModelProvider.list_llm_models()
        return BedrockModelProvider.list_llm_models()

    @classmethod
    def test(cls, model_name: str) -> Literal["ok"]:
        if CAIIModelProvider.is_enabled():
            models = cls.list_available()
            for model in models:
                if model.model_id == model_name:
                    if model.available:
                        return cls.test_llm_chat(model_name)
                    else:
                        raise HTTPException(status_code=503, detail="Model not ready")
        try:
            cls.get(model_name)
        except Exception:
            raise HTTPException(status_code=404, detail="Model not found")

        return cls.test_llm_chat(model_name)

    @classmethod
    def test_llm_chat(cls, model_name: str) -> Literal["ok"]:
        cls.get(model_name).chat(
            messages=[
                ChatMessage(
                    role=MessageRole.USER,
                    content="Are you available to answer questions?",
                )
            ]
        )
        return "ok"


# ensure interface is implemented
_ = LLM()
