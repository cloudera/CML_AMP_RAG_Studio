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
import queue
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Optional, Generator, Any, cast

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from llama_index.core.base.llms.types import ChatResponse, MessageRole
from pydantic import BaseModel
from starlette.responses import ContentStream
from starlette.types import Receive

from app.services.chat.streaming_chat import stream_chat
from .... import exceptions
from ....rag_types import RagPredictConfiguration
from ....services.chat.chat import (
    chat as run_chat,
)
from ....services.chat_history.chat_history_manager import (
    RagStudioChatMessage,
    chat_history_manager,
)
from ....services.chat_history.paginator import paginate
from ....services.metadata_apis import session_metadata_api
from ....services.mlflow import rating_mlflow_log_metric, feedback_mlflow_log_table
from ....services.query.agents.tool_calling_querier import poison_pill
from ....services.query.chat_events import ChatEvent
from ....services.session import rename_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions/{session_id}", tags=["Sessions"])


class CancelableStreamingResponse(StreamingResponse):
    """
    A custom StreamingResponse that can detect client disconnection and cancel a running thread.
    """

    def __init__(
        self,
        content_generator: ContentStream,
        cancel_event: threading.Event,
        *args: Any,
        **kwargs: Any,
    ):
        self.cancel_event = cancel_event
        super().__init__(content_generator, *args, **kwargs)

    async def listen_for_disconnect(self, receive: Receive) -> None:
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                logger.info("Client disconnected, cancelling stream")
                self.cancel_event.set()
                break


class RagSuggestedQuestionsResponse(BaseModel):
    suggested_questions: list[str]


@router.post(
    "/rename-session",
    summary="Rename the session using AI",
)
@exceptions.propagates
def post_rename_session(
    session_id: int, origin_remote_user: Optional[str] = Header(None)
) -> str:
    return rename_session(session_id, user_name=origin_remote_user)


class RagStudioChatHistoryResponse(BaseModel):
    data: list[RagStudioChatMessage]
    next_id: Optional[int] = None
    previous_id: Optional[int] = None


@router.get(
    "/chat-history",
    summary="Returns an array of chat messages for the provided session, with optional pagination.",
)
@exceptions.propagates
def chat_history(
    session_id: int, limit: Optional[int] = None, offset: Optional[int] = None
) -> RagStudioChatHistoryResponse:
    results = chat_history_manager.retrieve_chat_history(session_id=session_id)

    paginated_results, previous_id, next_id = paginate(results, limit, offset)
    return RagStudioChatHistoryResponse(
        data=paginated_results,
        next_id=next_id,
        previous_id=previous_id,
    )


@router.get(
    "/chat-history/{message_id}",
    summary="Returns a specific chat messages for the provided session.",
)
@exceptions.propagates
def get_message_by_id(session_id: int, message_id: str) -> RagStudioChatMessage:
    results: list[RagStudioChatMessage] = chat_history_manager.retrieve_chat_history(
        session_id=session_id
    )
    for message in results:
        if message.id == message_id:
            return message
    raise HTTPException(
        status_code=404,
        detail=f"Message with id {message_id} not found in session {session_id}",
    )


@router.delete(
    "/chat-history", summary="Deletes the chat history for the provided session."
)
@exceptions.propagates
def clear_chat_history(session_id: int) -> str:
    chat_history_manager.clear_chat_history(session_id=session_id)
    return "Chat history cleared."


@router.delete("", summary="Deletes the requested session.")
@exceptions.propagates
def delete_session(session_id: int) -> str:
    chat_history_manager.delete_chat_history(session_id=session_id)
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
    origin_remote_user: Optional[str] = Header(None),
) -> ChatResponseRating:
    rating_mlflow_log_metric(
        request.rating, response_id, session_id, user_name=origin_remote_user
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
    origin_remote_user: Optional[str] = Header(None),
) -> ChatResponseFeedback:
    feedback_mlflow_log_table(
        request.feedback, response_id, session_id, user_name=origin_remote_user
    )
    return ChatResponseFeedback(feedback=request.feedback)


class RagStudioChatRequest(BaseModel):
    query: str
    configuration: RagPredictConfiguration | None = None


class StreamCompletionRequest(BaseModel):
    query: str


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
    origin_remote_user: Optional[str] = Header(None),
) -> RagStudioChatMessage:
    session = session_metadata_api.get_session(session_id, user_name=origin_remote_user)

    configuration = request.configuration or RagPredictConfiguration()
    return run_chat(session, request.query, configuration, user_name=origin_remote_user)


@router.post(
    "/stream-completion", summary="Stream completion responses for the given query"
)
@exceptions.propagates
def stream_chat_completion(
    session_id: int,
    request: RagStudioChatRequest,
    origin_remote_user: Optional[str] = Header(None),
) -> StreamingResponse:
    session = session_metadata_api.get_session(session_id, user_name=origin_remote_user)
    configuration = request.configuration or RagPredictConfiguration()

    chat_event_queue: queue.Queue[ChatEvent] = queue.Queue()
    # Create a cancellation event to signal when the client disconnects
    cancel_event = threading.Event()

    def tools_callback(chat_future: Future[Any]) -> Generator[str, None, None]:
        while True:
            # Check if client has disconnected
            if cancel_event.is_set():
                logger.info("Client disconnected, stopping tool callback")
                # Try to cancel the future if it's still running
                if not chat_future.done():
                    chat_future.cancel()
                break

            if chat_future.done() and (e := chat_future.exception()):
                raise e

            try:
                event_data = chat_event_queue.get(block=True, timeout=1.0)
                print(event_data)
                if event_data.type == poison_pill:
                    break
                event_json = json.dumps({"event": event_data.model_dump()})
                yield f"data: {event_json}\n\n"
            except queue.Empty:
                # Send a heartbeat event every second to keep the connection alive
                heartbeat = ChatEvent(
                    type="event", name="Processing", timestamp=time.time()
                )
                event_json = json.dumps({"event": heartbeat.model_dump()})
                yield f"data: {event_json}\n\n"
                time.sleep(1)

    def generate_stream() -> Generator[str, None, None]:
        response_id: str = ""
        executor = None
        future = None

        try:
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(
                stream_chat,
                session=session,
                query=request.query,
                configuration=configuration,
                user_name=origin_remote_user,
                chat_event_queue=chat_event_queue,
            )

            # If we get here and the cancel_event is set, the client has disconnected
            if cancel_event.is_set():
                logger.info("Client disconnected, not processing results")
                return

            first_message = True
            stream = future.result()
            for item in stream:
                response = cast(ChatResponse, item)
                # Check for cancellation between each response
                if cancel_event.is_set():
                    logger.info("Client disconnected during result processing")
                    break
                if "chat_event" in response.additional_kwargs:
                    chat_event = response.additional_kwargs.get("chat_event")
                    event_json = json.dumps({"event": chat_event.model_dump()})
                    yield f"data: {event_json}\n\n"
                    continue
                # send an initial message to let the client know the response stream is starting
                if first_message:
                    done = ChatEvent(type="done", name="agent_done", timestamp=time.time())
                    event_json = json.dumps({"event": done.model_dump()})
                    yield f"data: {event_json}\n\n"
                    first_message = False
                response_id = response.additional_kwargs["response_id"]
                json_delta = json.dumps({"text": response.delta})
                yield f"data: {json_delta}\n\n"

            if not cancel_event.is_set() and response_id:
                done = ChatEvent(type="done", name="chat_done", timestamp=time.time())
                event_json = json.dumps({"event": done.model_dump()})
                yield f"data: {event_json}\n\n"
                yield f'data: {{"response_id" : "{response_id}"}}\n\n'

        except TimeoutError:
            logger.exception("Timeout: Failed to stream chat completion")
            yield 'data: {{"error" : "Timeout: Failed to stream chat completion"}}\n\n'
        except Exception as e:
            logger.exception("Failed to stream chat completion")
            yield f'data: {{"error" : "{e}"}}\n\n'
        finally:
            # Clean up resources
            if future and not future.done():
                future.cancel()
            if executor:
                executor.shutdown(wait=False)

    return CancelableStreamingResponse(
        generate_stream(), cancel_event=cancel_event, media_type="text/event-stream"
    )
