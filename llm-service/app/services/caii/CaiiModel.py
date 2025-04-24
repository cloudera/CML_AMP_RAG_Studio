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
from typing import Callable, Dict, Sequence, Any

from llama_index.core.base.llms.types import ChatMessage, LLMMetadata, ChatResponse, CompletionResponse
from llama_index.llms.openai import OpenAI
from pydantic import Field


class CaiiModel(OpenAI):
    context: int = Field(
        description="The context size",
        gt=0,
    )

    def __init__(
        self,
        model: str,
        context: int,
        api_base: str,
        messages_to_prompt: Callable[[Sequence[ChatMessage]], str],
        completion_to_prompt: Callable[[str], str],
        default_headers: Dict[str, str],
    ):
        super().__init__(
            model=model,
            api_base=api_base,
            messages_to_prompt=messages_to_prompt,
            completion_to_prompt=completion_to_prompt,
            default_headers=default_headers,
            context=context,
        )
        self.context = context

    @property
    def metadata(self) -> LLMMetadata:
        ## todo: pull this info from somewhere
        return LLMMetadata(
            context_window=self.context,
            num_output=self.max_tokens or -1,
            is_chat_model=True,
            is_function_calling_model=True,
            model_name=self.model,
        )

class DeepseekModel(CaiiModel):
    def __init__(
            self,
            model: str,
            context: int,
            api_base: str,
            messages_to_prompt: Callable[[Sequence[ChatMessage]], str],
            completion_to_prompt: Callable[[str], str],
            default_headers: Dict[str, str],
    ):
        super().__init__(
            model=model,
            api_base=api_base,
            messages_to_prompt=messages_to_prompt,
            completion_to_prompt=completion_to_prompt,
            default_headers=default_headers,
            context=context,
        )

    def complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        completion: CompletionResponse = super().complete(prompt, formatted, **kwargs)
        completion.text = completion.text.split("</think>")[-1]
        return completion

    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        raw_response: ChatResponse = super().chat(messages, **kwargs)
        content: str = raw_response.message.content or ""
        raw_response.message.content = content.split("</think>")[-1]
        return raw_response

print(f'services/caii/CaiiModel.py took {time.time() - start_time:.3f} seconds to import')
