# ##############################################################################
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
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
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
# ##############################################################################
import time
import uuid
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .... import exceptions
from ....rag_types import RagPredictConfiguration
from ....services import llm_completion
from ....services.chat import generate_suggested_questions, v2_chat
from ....services.chat_store import ChatHistoryManager, RagStudioChatMessage, RagMessage
from ....services.metadata_apis import session_metadata_api

router = APIRouter(prefix="/sessions/{session_id}", tags=["Sessions"])


@router.get(
    "/chat-history",
    summary="Returns an array of chat messages for the provided session.",
)
@exceptions.propagates
def chat_history(session_id: int) -> list[RagStudioChatMessage]:
    return ChatHistoryManager().retrieve_chat_history(session_id=session_id)


@router.delete(
    "/chat-history", summary="Deletes the chat history for the provided session."
)
@exceptions.propagates
def clear_chat_history(session_id: int) -> str:
    ChatHistoryManager().clear_chat_history(session_id=session_id)
    return "Chat history cleared."


@router.delete("", summary="Deletes the requested session.")
@exceptions.propagates
def delete_chat_history(session_id: int) -> str:
    ChatHistoryManager().delete_chat_history(session_id=session_id)
    return "Chat history deleted."


class RagStudioChatRequest(BaseModel):
    query: str
    configuration: RagPredictConfiguration | None = None


@router.post("/chat", summary="Chat with your documents in the requested datasource")
@exceptions.propagates
def chat(
        session_id: int,
        request: RagStudioChatRequest,
) -> RagStudioChatMessage:
    configuration = request.configuration or RagPredictConfiguration()
    if configuration.exclude_knowledge_base:
        return llm_talk(session_id, request.query)
    return v2_chat(session_id, request.query, configuration)


def llm_talk(
        session_id: int,
        query: str,
) -> RagStudioChatMessage:
    session = session_metadata_api.get_session(session_id)
    chat_response = llm_completion.completion(
        session_id, query, session.inference_model
    )
    new_chat_message = RagStudioChatMessage(
        id=str(uuid.uuid4()),
        source_nodes=[],
        inference_model=session.inference_model,
        evaluations=[],
        rag_message=RagMessage(
            user=query,
            assistant=str(chat_response.message.content),
        ),
        timestamp=time.time(),
    )
    ChatHistoryManager().append_to_history(session_id, [new_chat_message])
    return new_chat_message


class RagSuggestedQuestionsResponse(BaseModel):
    suggested_questions: list[str]


@router.post("/suggest-questions", summary="Suggest questions with context")
@exceptions.propagates
def suggest_questions(
        session_id: int,
) -> RagSuggestedQuestionsResponse:
    suggested_questions = generate_suggested_questions(session_id)
    return RagSuggestedQuestionsResponse(suggested_questions=suggested_questions)
