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
from typing import List

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.storage.chat_store import SimpleChatStore

from app.config import settings
from app.services.chat_history.chat_history_manager import (
    ChatHistoryManager,
    RagMessage,
    RagStudioChatMessage,
)


class SimpleChatHistoryManager(ChatHistoryManager):
    @property
    def store_path(self) -> str:
        return settings.rag_databases_dir

    def retrieve_chat_history(self, session_id: int) -> List[RagStudioChatMessage]:
        """Retrieve chat history for a session.

        Args:
            session_id: The ID of the session to retrieve chat history for.

        Returns:
            A list of chat messages, optionally paginated.
        """
        store = self._store_for_session(session_id)

        messages: list[ChatMessage] = store.get_messages(
            self._build_chat_key(session_id)
        )
        results: list[RagStudioChatMessage] = []

        i = 0
        while i < len(messages):
            user_message = messages[i]
            # todo: handle the possibility of falling off the end of the list.
            assistant_message = messages[i + 1]
            # if we are somehow in a bad state, correct it with an empty assistant message and back up the index by one
            if assistant_message.role == MessageRole.USER:
                assistant_message = ChatMessage()
                assistant_message.role = MessageRole.ASSISTANT
                assistant_message.content = ""
                i = i - 1
            results.append(
                RagStudioChatMessage(
                    id=user_message.additional_kwargs["id"],
                    session_id=session_id,
                    source_nodes=assistant_message.additional_kwargs.get(
                        "source_nodes", []
                    ),
                    inference_model=assistant_message.additional_kwargs.get(
                        "inference_model", None
                    ),
                    rag_message=RagMessage(
                        user=str(user_message.content),
                        assistant=str(assistant_message.content),
                    ),
                    evaluations=assistant_message.additional_kwargs.get(
                        "evaluations", []
                    ),
                    timestamp=assistant_message.additional_kwargs.get("timestamp", 0.0),
                    condensed_question=None,
                )
            )
            i += 2

        return results

    def _store_for_session(self, session_id: int) -> SimpleChatStore:
        store = SimpleChatStore.from_persist_path(
            persist_path=self._store_file(session_id)
        )
        return store

    def clear_chat_history(self, session_id: int) -> None:
        store = self._store_for_session(session_id)
        store.delete_messages(self._build_chat_key(session_id))
        store.persist(self._store_file(session_id))

    def delete_chat_history(self, session_id: int) -> None:
        session_storage = self._store_file(session_id)
        if os.path.exists(session_storage):
            os.remove(session_storage)

    def _store_file(self, session_id: int) -> str:
        return os.path.join(self.store_path, f"chat_store-{session_id}.json")

    def append_to_history(
        self, session_id: int, messages: List[RagStudioChatMessage]
    ) -> None:
        store = self._store_for_session(session_id)

        for message in messages:
            store.add_message(
                self._build_chat_key(session_id),
                ChatMessage(
                    role=MessageRole.USER,
                    content=message.rag_message.user,
                    additional_kwargs={
                        "id": message.id,
                    },
                ),
            )
            store.add_message(
                self._build_chat_key(session_id),
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=message.rag_message.assistant,
                    additional_kwargs={
                        "id": message.id,
                        "source_nodes": message.source_nodes,
                        "inference_model": message.inference_model,
                        "evaluations": message.evaluations,
                        "timestamp": message.timestamp,
                    },
                ),
            )
            store.persist(self._store_file(session_id))

    def update_message(
        self, session_id: int, message_id: str, message: RagStudioChatMessage
    ) -> None:
        """Update an existing message's user/assistant content and metadata by ID."""
        store = self._store_for_session(session_id)
        key = self._build_chat_key(session_id)
        messages: list[ChatMessage] = store.get_messages(key)

        # Each logical message is stored as a pair: USER, ASSISTANT with same id
        for i in range(0, len(messages), 2):
            user_msg = messages[i]
            if user_msg.additional_kwargs.get("id") == message_id:
                # Update user content
                user_msg.content = message.rag_message.user
                # Update assistant content and metadata (next message)
                if i + 1 < len(messages):
                    assistant_msg = messages[i + 1]
                else:
                    assistant_msg = ChatMessage(role=MessageRole.ASSISTANT, content="")
                    messages.append(assistant_msg)
                assistant_msg.content = message.rag_message.assistant
                assistant_msg.additional_kwargs.update(
                    {
                        "id": message_id,
                        "source_nodes": message.source_nodes,
                        "inference_model": message.inference_model,
                        "evaluations": message.evaluations,
                        "timestamp": message.timestamp,
                    }
                )
                # Persist updated list
                store.delete_messages(key)
                for m in messages:
                    store.add_message(key, m)
                store.persist(self._store_file(session_id))
                return

    def delete_message(self, session_id: int, message_id: str) -> None:
        """Delete both USER and ASSISTANT entries for a given message id."""
        store = self._store_for_session(session_id)
        key = self._build_chat_key(session_id)
        messages: list[ChatMessage] = store.get_messages(key)

        new_messages: list[ChatMessage] = []
        i = 0
        while i < len(messages):
            user_msg = messages[i]
            assistant_msg = messages[i + 1] if i + 1 < len(messages) else None
            current_id = user_msg.additional_kwargs.get("id")
            if current_id != message_id:
                new_messages.append(user_msg)
                if assistant_msg is not None:
                    new_messages.append(assistant_msg)
            i += 2

        store.delete_messages(key)
        for m in new_messages:
            store.add_message(key, m)
        store.persist(self._store_file(session_id))

    @staticmethod
    def _build_chat_key(session_id: int) -> str:
        return "session_" + str(session_id)
