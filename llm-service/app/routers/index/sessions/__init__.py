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

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from pydantic import BaseModel

from .... import exceptions
from ....ai.vector_stores.qdrant import QdrantVectorStore
from ....rag_types import RagPredictConfiguration
from ....services import llm_completion
from ....services.chat import generate_suggested_questions, v2_chat, v2_chat_streaming
from ....services.chat_store import ChatHistoryManager, RagStudioChatMessage

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


async def chat_stream(session_id, request):
    contents = llm_talk_streaming(session_id, request)
    for content in contents:
        yield f"{content}"

    yield "\n"
    yield f"chunks\n"
    yield f"evaluations\n"

async def full_chat_stream(stream: StreamingAgentChatResponse):
    for message in stream.chat_stream:
        yield f"data: {message.delta}\n\n"
    # for chunk in chunks:
    #     yield f"data: {chunk}\n\n"


@router.post("/chat-es", summary="Chat with your documents in the requested datasource")
@exceptions.propagates
async def chat_es(
    session_id: int,
    request: RagStudioChatRequest,
) -> StreamingResponse:
    if request.configuration.exclude_knowledge_base:
        return StreamingResponse(media_type="text/event-stream", content=chat_stream(session_id, request))

    stream = v2_chat_streaming(session_id, request.data_source_ids, request.query, request.configuration)
    return StreamingResponse(media_type="text/event-stream", content=map(lambda x: x.delta, stream.chat_stream))

def llm_talk_streaming(
        session_id: int,
        request: RagStudioChatRequest,
):
    chat_response = llm_completion.completion_streaming(
        session_id, request.query, request.configuration
    )

    for x in chat_response:
        yield x.delta


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
