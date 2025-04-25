#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
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

from abc import ABCMeta, abstractmethod
from typing import Optional, Literal

from pydantic import BaseModel


class RagPredictSourceNode(BaseModel):
    node_id: str
    doc_id: str
    source_file_name: str
    score: float
    dataSourceId: Optional[int] = None


class Evaluation(BaseModel):
    name: Literal["relevance", "faithfulness"]
    value: float


class RagMessage(BaseModel):
    user: str
    assistant: str


class RagStudioChatMessage(BaseModel):
    id: str
    session_id: int
    source_nodes: list[RagPredictSourceNode]
    inference_model: Optional[str]  # `None` for legacy data or no chunks
    rag_message: RagMessage
    evaluations: list[Evaluation]
    timestamp: float
    condensed_question: Optional[str]


class ChatHistoryManager(metaclass=ABCMeta):
    @abstractmethod
    def retrieve_chat_history(self, session_id):
        pass

    @abstractmethod
    def clear_chat_history(self, session_id):
        pass

    @abstractmethod
    def delete_chat_history(self, session_id):
        pass

    @abstractmethod
    def append_to_history(self, session_id, messages: list[RagStudioChatMessage]):
        pass


def create() -> ChatHistoryManager:
    from app.services.chat_history.chat_store import SimpleChatHistoryManager

    return SimpleChatHistoryManager()
