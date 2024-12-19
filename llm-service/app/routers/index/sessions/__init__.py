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
import logging
import time
import uuid
from collections.abc import Generator

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from llama_index.core.base.llms.types import ChatResponse

from .... import exceptions
from ....ai.vector_stores.qdrant import QdrantVectorStore
from ....rag_types import RagPredictConfiguration
from ....services import llm_completion
from ....services.chat import generate_suggested_questions, v2_chat
from ....services.chat_store import ChatHistoryManager, RagStudioChatMessage
from fastapi.responses import StreamingResponse
import json
from pydantic import BaseModel
from typing import List, Optional

class ClientAttachment(BaseModel):
    name: str
    contentType: str
    url: str


class ToolInvocation(BaseModel):
    toolCallId: str
    toolName: str
    args: dict
    result: dict


class ClientMessage(BaseModel):
    role: str
    content: str
    experimental_attachments: Optional[List[ClientAttachment]] = None
    toolInvocations: Optional[List[ToolInvocation]] = None


def convert_to_openai_messages(messages: List[ClientMessage]):
    openai_messages = []

    for message in messages:
        parts = []

        parts.append({
            'type': 'text',
            'text': message.content
        })

        if (message.experimental_attachments):
            for attachment in message.experimental_attachments:
                if (attachment.contentType.startswith('image')):
                    parts.append({
                        'type': 'image_url',
                        'image_url': {
                            'url': attachment.url
                        }
                    })

                elif (attachment.contentType.startswith('text')):
                    parts.append({
                        'type': 'text',
                        'text': attachment.url
                    })

        if (message.toolInvocations):
            tool_calls = [
                {
                    'id': tool_invocation.toolCallId,
                    'type': 'function',
                    'function': {
                        'name': tool_invocation.toolName,
                        'arguments': json.dumps(tool_invocation.args)
                    }
                }
                for tool_invocation in message.toolInvocations]

            openai_messages.append({
                "role": 'assistant',
                "tool_calls": tool_calls
            })

            tool_results = [
                {
                    'role': 'tool',
                    'content': json.dumps(tool_invocation.result),
                    'tool_call_id': tool_invocation.toolCallId
                }
                for tool_invocation in message.toolInvocations]

            openai_messages.extend(tool_results)

            continue

        openai_messages.append({
            "role": message.role,
            "content": parts
        })

    return openai_messages

router = APIRouter(prefix="/sessions/{session_id}", tags=["Sessions"])

logger = logging.getLogger(__name__)


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
    data_source_ids: list[int]
    query: str
    configuration: RagPredictConfiguration


@router.post("/chat", summary="Chat with your documents in the requested datasource")
@exceptions.propagates
def chat(
    session_id: int,
    request: RagStudioChatRequest,
) -> RagStudioChatMessage:
    if request.configuration.exclude_knowledge_base:
        return llm_talk(session_id, request)
    return v2_chat(
        session_id, request.data_source_ids, request.query, request.configuration
    )


def llm_talk(
    session_id: int,
    request: RagStudioChatRequest,
) -> RagStudioChatMessage:
    chat_response = llm_completion.completion(
        session_id, request.query, request.configuration
    )
    new_chat_message = RagStudioChatMessage(
        id=str(uuid.uuid4()),
        source_nodes=[],
        inference_model=request.configuration.model_name,
        evaluations=[],
        rag_message={
            "user": request.query,
            "assistant": str(chat_response.message.content),
        },
        timestamp=time.time(),
    )
    ChatHistoryManager().append_to_history(session_id, [new_chat_message])
    return new_chat_message


class SuggestQuestionsRequest(BaseModel):
    data_source_ids: list[int]
    configuration: RagPredictConfiguration = RagPredictConfiguration()


class RagSuggestedQuestionsResponse(BaseModel):
    suggested_questions: list[str]


@router.post("/suggest-questions", summary="Suggest questions with context")
@exceptions.propagates
def suggest_questions(
    session_id: int,
    request: SuggestQuestionsRequest,
) -> RagSuggestedQuestionsResponse:

    if len(request.data_source_ids) != 1:
        raise HTTPException(
            status_code=400,
            detail="Only one datasource is supported for question suggestion.",
        )

    total_data_sources_size: int = sum(
        map(
            lambda ds_id: QdrantVectorStore.for_chunks(ds_id).size() or 0,
            request.data_source_ids,
        )
    )
    if total_data_sources_size == 0:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")
    suggested_questions = generate_suggested_questions(
        request.configuration,
        request.data_source_ids,
        total_data_sources_size,
        session_id,
    )
    return RagSuggestedQuestionsResponse(suggested_questions=suggested_questions)


def streaming_llm_talk(
        session_id: int,
        request: RagStudioChatRequest,
) -> Generator[ChatResponse, None, None]:
    return llm_completion.streaming_completion(
        session_id, request.query, request.configuration
    )


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        print('websocket accepted')
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        print('websocket disconnected')
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        session_id: int,
):
    await manager.connect(websocket)
    print('websocket accepted')
    try:
        while True:
            print('waiting for data')
            data = await websocket.receive_text()
            request = RagStudioChatRequest(
                data_source_ids=[1],
                query=data,
                configuration=RagPredictConfiguration(),
            )
            res = streaming_llm_talk(session_id, request)
            for x in res:
                print(x.delta)
                await websocket.send_text(x.delta)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info('websocket disconnected')

class Request(BaseModel):
    messages: List[ClientMessage]


def stream_text(messages: List[ClientMessage], protocol: str = 'data'):
    stream = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        stream=True,
    )

    # When protocol is set to "text", you will send a stream of plain text chunks
    # https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol#text-stream-protocol

    if (protocol == 'text'):
        for chunk in stream:
            for choice in chunk.choices:
                if choice.finish_reason == "stop":
                    break
                else:
                    yield "{text}".format(text=choice.delta.content)

    # When protocol is set to "data", you will send a stream data part chunks
    # https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol#data-stream-protocol

    elif (protocol == 'data'):
        draft_tool_calls = []
        draft_tool_calls_index = -1

        for chunk in stream:
            for choice in chunk.choices:
                if choice.finish_reason == "stop":
                    continue

                else:
                    yield '0:{text}\n'.format(text=json.dumps(choice.delta.content))

            if chunk.choices == []:
                usage = chunk.usage
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens

                yield 'd:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}}}}\n'.format(
                    reason="tool-calls" if len(
                        draft_tool_calls) > 0 else "stop",
                    prompt=prompt_tokens,
                    completion=completion_tokens
                )


@router.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query('data')):
    messages = request.messages
    openai_messages = convert_to_openai_messages(messages)

    response = StreamingResponse(stream_text(openai_messages, protocol))
    response.headers['x-vercel-ai-data-stream'] = 'v1'
    return response