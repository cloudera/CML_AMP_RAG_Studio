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
import time
import uuid
from contextlib import AbstractContextManager
from typing import Callable, cast
from unittest.mock import patch

from app.services.chat_history.chat_history_manager import (
    ChatHistoryManager,
    RagStudioChatMessage,
    RagMessage,
)
from app.services.models.providers import get_provider_class


class TestingChatHistoryManager(ChatHistoryManager):
    def __init__(self) -> None:
        self._chat_history: dict[int, list[RagStudioChatMessage]] = dict()

    def retrieve_chat_history(self, session_id: int) -> list[RagStudioChatMessage]:
        return self._chat_history.get(session_id, [])

    def clear_chat_history(self, session_id: int) -> None:
        self._chat_history[session_id] = []

    def delete_chat_history(self, session_id: int) -> None:
        del self._chat_history[session_id]

    def append_to_history(
        self, session_id: int, messages: list[RagStudioChatMessage]
    ) -> None:
        self._chat_history.setdefault(session_id, []).extend(messages)


# TODO: we might want to specifically patch S3 and Simple to test their implementations
def patch_get_chat_history_manager() -> (
    AbstractContextManager[Callable[[], TestingChatHistoryManager]]
):
    session_id = 1
    testing_chat_history_manager = TestingChatHistoryManager()
    testing_chat_history_manager.append_to_history(
        session_id,
        [
            RagStudioChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                source_nodes=[],
                inference_model=get_provider_class()
                .list_llm_models()[0]  # TODO: randomize?
                .model_id,
                rag_message=RagMessage(user="test question", assistant="test answer"),
                evaluations=[],
                timestamp=time.time(),
                condensed_question=None,
            )
        ],
    )

    return cast(
        AbstractContextManager[Callable[[], TestingChatHistoryManager]],
        patch(
            "app.services.chat_history.chat_history_manager._get_chat_history_manager",
            new=lambda: testing_chat_history_manager,
        ),
    )
