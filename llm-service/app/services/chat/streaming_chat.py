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
from typing import Optional, Generator

from llama_index.core.base.llms.types import ChatResponse, ChatMessage
from llama_index.core.chat_engine.types import (
    AgentChatResponse,
    StreamingAgentChatResponse,
)

from app.ai.vector_stores.vector_store_factory import VectorStoreFactory
from app.rag_types import RagPredictConfiguration
from app.services import llm_completion, models, evaluators
from app.services.chat.utils import retrieve_chat_history, format_source_nodes
from app.services.chat_history.chat_history_manager import (
    RagStudioChatMessage,
    RagMessage,
    chat_history_manager, Evaluation,
)
from app.services.metadata_apis.session_metadata_api import Session
from app.services.mlflow import record_direct_llm_mlflow_run, record_rag_mlflow_run
from app.services.query import querier
from app.services.query.chat_engine import (
    FlexibleContextChatEngine,
    build_flexible_chat_engine,
)
from app.services.query.querier import (
    build_retriever, get_nodes_from_output,
)
from app.services.query.query_configuration import QueryConfiguration


def stream_chat(
    session: Session,
    query: str,
    configuration: RagPredictConfiguration,
    user_name: Optional[str],
    response_id: Optional[str] = None,
) -> Generator[ChatResponse, None, None]:
    query_configuration = QueryConfiguration(
        top_k=session.response_chunks,
        model_name=session.inference_model,
        rerank_model_name=session.rerank_model,
        exclude_knowledge_base=configuration.exclude_knowledge_base,
        use_question_condensing=configuration.use_question_condensing,
        use_hyde=session.query_configuration.enable_hyde,
        use_summary_filter=session.query_configuration.enable_summary_filter,
        use_tool_calling=session.query_configuration.enable_tool_calling,
        use_streaming=not session.query_configuration.disable_streaming,
    )

    response_id = response_id or str(uuid.uuid4())
    new_chat_message = RagStudioChatMessage(
        id=response_id,
        session_id=session.id,
        source_nodes=[],
        inference_model=session.inference_model,
        evaluations=[],
        rag_message=RagMessage(
            user=query,
            assistant="",
        ),
        timestamp=time.time(),
        condensed_question=None,
    )
    chat_history_manager.append_to_history(session.id, [new_chat_message])

    total_data_sources_size: int = sum(
        map(
            lambda ds_id: VectorStoreFactory.for_chunks(ds_id).size() or 0,
            session.get_all_data_source_ids(),
        )
    )
    if not query_configuration.use_tool_calling and (
        len(session.get_all_data_source_ids()) == 0 or total_data_sources_size == 0
    ):
        # put a poison pill in the queue to stop the tool events stream
        return _stream_direct_llm_chat(session, response_id, query, user_name)

    condensed_question, streaming_chat_response = build_streamer(
        query, query_configuration, session
    )

    return _run_streaming_chat(
        session,
        response_id,
        query,
        query_configuration,
        user_name,
        condensed_question=condensed_question,
        streaming_chat_response=streaming_chat_response,
    )


def _run_streaming_chat(
    session: Session,
    response_id: str,
    query: str,
    query_configuration: QueryConfiguration,
    user_name: Optional[str],
    streaming_chat_response: StreamingAgentChatResponse,
    condensed_question: Optional[str] = None,
) -> Generator[ChatResponse, None, None]:
    response: ChatResponse = ChatResponse(message=ChatMessage(content=query))
    if streaming_chat_response.chat_stream:
        for response in streaming_chat_response.chat_stream:
            response.additional_kwargs["response_id"] = response_id
            yield response

    chat_response = AgentChatResponse(
        response=response.message.content or "",
        sources=streaming_chat_response.sources,
        source_nodes=streaming_chat_response.source_nodes,
    )

    finalize_response(
        chat_response,
        condensed_question,
        query,
        query_configuration,
        response_id,
        session,
        user_name,
    )


def build_streamer(
    query: str,
    query_configuration: QueryConfiguration,
    session: Session,
) -> tuple[str | None, StreamingAgentChatResponse]:
    llm = models.LLM.get(model_name=query_configuration.model_name)

    retriever = build_retriever(
        query_configuration, session.get_all_data_source_ids(), llm
    )

    chat_engine: Optional[FlexibleContextChatEngine] = build_flexible_chat_engine(
        query_configuration, llm, retriever
    )
    chat_history = retrieve_chat_history(session.id)
    chat_messages = list(
        map(
            lambda message: ChatMessage(role=message.role, content=message.content),
            chat_history,
        )
    )
    condensed_question = (
        chat_engine.condense_question(chat_messages, query).strip()
        if chat_engine
        else None
    )
    streaming_chat_response = querier.streaming_query(
        chat_engine,
        query,
        query_configuration,
        chat_messages,
        session=session,
    )
    return condensed_question, streaming_chat_response


def _stream_direct_llm_chat(
    session: Session,
    response_id: str,
    query: str,
    user_name: Optional[str],
) -> Generator[ChatResponse, None, None]:
    record_direct_llm_mlflow_run(response_id, session, user_name)
    response: ChatResponse
    if session.query_configuration.disable_streaming:
        # Use non-streaming completion when streaming is disabled
        response = llm_completion.completion(session.id, query, session.inference_model)
        response.additional_kwargs["response_id"] = response_id
        yield response
    else:
        chat_response = llm_completion.stream_completion(
            session.id, query, session.inference_model
        )
        response = ChatResponse(message=ChatMessage(content=query))
        for response in chat_response:
            response.additional_kwargs["response_id"] = response_id
            yield response

    new_chat_message = RagStudioChatMessage(
        id=response_id,
        session_id=session.id,
        source_nodes=[],
        inference_model=session.inference_model,
        evaluations=[],
        rag_message=RagMessage(
            user=query,
            assistant=response.message.content or "",
        ),
        timestamp=time.time(),
        condensed_question=None,
    )
    chat_history_manager.update_message(session.id, response_id, new_chat_message)


def finalize_response(
    chat_response: AgentChatResponse,
    condensed_question: str | None,
    query: str,
    query_configuration: QueryConfiguration,
    response_id: str,
    session: Session,
    user_name: Optional[str],
) -> RagStudioChatMessage:
    if condensed_question and (condensed_question.strip() == query.strip()):
        condensed_question = None

    orig_source_nodes = chat_response.source_nodes
    source_nodes = get_nodes_from_output(chat_response.response, session)

    # if node with id present in orig_source_nodes, then don't add it again
    node_ids_present = set([node.node_id for node in orig_source_nodes])
    for node in source_nodes:
        if node.node_id not in node_ids_present:
            orig_source_nodes.append(node)

    chat_response.source_nodes = orig_source_nodes

    evaluations = []
    if len(chat_response.source_nodes) != 0:
        relevance, faithfulness = evaluators.evaluate_response(
            query, chat_response, session.inference_model
        )
        evaluations.append(Evaluation(name="relevance", value=relevance))
        evaluations.append(Evaluation(name="faithfulness", value=faithfulness))
    response_source_nodes = format_source_nodes(chat_response)
    new_chat_message = RagStudioChatMessage(
        id=response_id,
        session_id=session.id,
        source_nodes=response_source_nodes,
        inference_model=session.inference_model,
        rag_message=RagMessage(
            user=query,
            assistant=chat_response.response,
        ),
        evaluations=evaluations,
        timestamp=time.time(),
        condensed_question=condensed_question,
    )
    record_rag_mlflow_run(
        new_chat_message, query_configuration, response_id, session, user_name
    )
    chat_history_manager.update_message(session.id, response_id, new_chat_message)

    return new_chat_message
