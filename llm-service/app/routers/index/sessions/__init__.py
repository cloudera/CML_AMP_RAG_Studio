import time
start_time = time.time()
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
import base64
import json
import logging
from typing import Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel

from .... import exceptions
from ....rag_types import RagPredictConfiguration
from ....services.chat import (
    v2_chat,
)
from ....services.chat_store import ChatHistoryManager, RagStudioChatMessage
from ....services.metadata_apis import session_metadata_api
from ....services.mlflow import rating_mlflow_log_metric, feedback_mlflow_log_table
from ....services.session import rename_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions/{session_id}", tags=["Sessions"])


class RagSuggestedQuestionsResponse(BaseModel):
    suggested_questions: list[str]


@router.post(
    "/rename-session",
    summary="Rename the session using AI",
)
@exceptions.propagates
def post_rename_session(
    session_id: int, remote_user: Optional[str] = Header(None)
) -> str:
    return rename_session(session_id, user_name=remote_user)


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


class ChatResponseRating(BaseModel):
    rating: bool


@router.post(
    "/responses/{response_id}/rating", summary="Provide a rating on a chat response."
)
@exceptions.propagates
def rating(
    session_id: int,
    response_id: str,
    request: ChatResponseRating,
    remote_user: Optional[str] = Header(None),
) -> ChatResponseRating:
    rating_mlflow_log_metric(
        request.rating, response_id, session_id, user_name=remote_user
    )
    return ChatResponseRating(rating=request.rating)


class ChatResponseFeedback(BaseModel):
    feedback: str


@router.post(
    "/responses/{response_id}/feedback", summary="Provide feedback on a chat response."
)
@exceptions.propagates
def feedback(
    session_id: int,
    response_id: str,
    request: ChatResponseFeedback,
    remote_user: Optional[str] = Header(None),
) -> ChatResponseFeedback:
    feedback_mlflow_log_table(
        request.feedback, response_id, session_id, user_name=remote_user
    )
    return ChatResponseFeedback(feedback=request.feedback)


class RagStudioChatRequest(BaseModel):
    query: str
    configuration: RagPredictConfiguration | None = None


def parse_jwt_cookie(jwt_cookie: str | None) -> str:
    if jwt_cookie is None:
        return "unknown"
    try:
        cookie_crumbs = jwt_cookie.strip().split(".")
        if len(cookie_crumbs) != 3:
            return "unknown"
        base_64_user_info = cookie_crumbs[1]
        user_info_json = base64.b64decode(base_64_user_info + "===")
        user_info = json.loads(user_info_json)
        return str(user_info["username"])
    except Exception:
        logger.exception("Failed to parse JWT cookie")
        return "unknown"


@router.post("/chat", summary="Chat with your documents in the requested datasource")
@exceptions.propagates
def chat(
    session_id: int,
    request: RagStudioChatRequest,
    remote_user: Optional[str] = Header(None),
) -> RagStudioChatMessage:
    session = session_metadata_api.get_session(session_id, user_name=remote_user)

    configuration = request.configuration or RagPredictConfiguration()
    return v2_chat(session, request.query, configuration, user_name=remote_user)

print('routers/index/sessions/__init__.py took {time.time() - start_time} seconds to import')
