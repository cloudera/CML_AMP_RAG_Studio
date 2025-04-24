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
from typing import Sequence, Any

from llama_index.core.base.embeddings.base import BaseEmbedding, Embedding
from llama_index.core.base.llms.types import (
    LLMMetadata,
    ChatMessage,
    ChatResponse,
    CompletionResponse,
    ChatResponseGen,
    CompletionResponseGen,
    ChatResponseAsyncGen,
    CompletionResponseAsyncGen,
)
from llama_index.core.llms import LLM
from pydantic import Field


class DummyEmbeddingModel(BaseEmbedding):
    def _get_query_embedding(self, query: str) -> Embedding:
        return []

    async def _aget_query_embedding(self, query: str) -> Embedding:
        return []

    def _get_text_embedding(self, text: str) -> Embedding:
        return []


class DummyLlm(LLM):
    completion_response: str = Field("this is a completion response")
    chat_response: str = Field("this is a chat response")

    def __init__(
        self,
        completion_response: str = "this is a completion response",
        chat_response: str = "hello",
    ):
        super().__init__()
        self.completion_response = completion_response
        self.chat_response = chat_response

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata()

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        return ChatResponse(message=ChatMessage.from_str(self.chat_response))

    def complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponse:
        return CompletionResponse(text=self.completion_response)

    def stream_chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponseGen:
        raise NotImplementedError("Not implemented")

    def stream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseGen:
        raise NotImplementedError("Not implemented")

    async def achat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponse:
        raise NotImplementedError("Not implemented")

    async def acomplete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponse:
        raise NotImplementedError("Not implemented")

    async def astream_chat(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponseAsyncGen:
        raise NotImplementedError("Not implemented")

    async def astream_complete(
        self, prompt: str, formatted: bool = False, **kwargs: Any
    ) -> CompletionResponseAsyncGen:
        raise NotImplementedError("Not implemented")

print('services/models/_noop.py took {time.time() - start_time} seconds to import')
