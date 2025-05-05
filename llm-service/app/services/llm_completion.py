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
import itertools
from typing import Generator

from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
    ChatResponseGen,
)
from llama_index.core.llms import LLM

from . import models
from .chat_history.chat_history_manager import (
    RagStudioChatMessage,
    chat_history_manager,
)
from .query.query_configuration import QueryConfiguration


def make_chat_messages(x: RagStudioChatMessage) -> list[ChatMessage]:
    user = ChatMessage.from_str(x.rag_message.user, role="user")
    assistant = ChatMessage.from_str(x.rag_message.assistant, role="assistant")
    return [user, assistant]


def completion(session_id: int, question: str, model_name: str) -> ChatResponse:
    model = models.LLM.get(model_name)
    chat_history = chat_history_manager.retrieve_chat_history(session_id)[:10]
    messages = list(
        itertools.chain.from_iterable(
            map(lambda x: make_chat_messages(x), chat_history)
        )
    )
    messages.append(ChatMessage.from_str(question, role="user"))
    return model.chat(messages)


def stream_completion(
    session_id: int, question: str, model_name: str
) -> Generator[ChatResponse, None, None]:
    """
    Streamed version of the completion function.
    Returns a generator that yields ChatResponse objects as they become available.
    """
    model = models.LLM.get(model_name)
    chat_history = chat_history_manager.retrieve_chat_history(session_id)[:10]
    messages = list(
        itertools.chain.from_iterable(
            map(lambda x: make_chat_messages(x), chat_history)
        )
    )
    messages.append(ChatMessage.from_str(question, role="user"))

    stream = model.stream_chat(messages)
    return stream


def hypothetical(question: str, configuration: QueryConfiguration) -> str:
    model: LLM = models.LLM.get(configuration.model_name)
    prompt: str = (
        f"You are an expert. You are asked: {question}. "
        "Produce a brief document that would hypothetically answer this question."
    )
    return model.complete(prompt).text
