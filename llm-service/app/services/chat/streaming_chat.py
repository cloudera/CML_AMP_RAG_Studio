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
import queue
import time
import uuid
from typing import Optional, Generator

from llama_index.core.base.llms.types import ChatResponse, ChatMessage
from llama_index.core.chat_engine.types import AgentChatResponse

from app.rag_types import RagPredictConfiguration
from app.services import evaluators, llm_completion
from app.services.chat.utils import retrieve_chat_history, format_source_nodes
from app.services.chat_history.chat_history_manager import (
    RagStudioChatMessage,
    RagMessage,
    Evaluation,
    chat_history_manager,
)
from app.services.metadata_apis.session_metadata_api import Session
from app.services.mlflow import record_rag_mlflow_run, record_direct_llm_mlflow_run
from app.services.query import querier
from app.services.query.query_configuration import QueryConfiguration


def stream_chat(session: Session, query: str, configuration: RagPredictConfiguration, user_name: Optional[str],
                crew_events_queue: queue.Queue) -> Generator[ChatResponse| str, None, None]:
    query_configuration = QueryConfiguration(
        top_k=session.response_chunks,
        model_name=session.inference_model,
        rerank_model_name=session.rerank_model,
        exclude_knowledge_base=configuration.exclude_knowledge_base,
        use_question_condensing=configuration.use_question_condensing,
        use_hyde=session.query_configuration.enable_hyde,
        use_summary_filter=session.query_configuration.enable_summary_filter,
        use_tool_calling=session.query_configuration.enable_tool_calling,
    )

    response_id = str(uuid.uuid4())

    if not query_configuration.use_tool_calling and not session.data_source_ids:
        return _stream_direct_llm_chat(session, response_id, query, user_name)

    # total_data_sources_size: int = sum(
    #     map(
    #         lambda ds_id: VectorStoreFactory.for_chunks(ds_id).size() or 0,
    #         session.data_source_ids,
    #     )
    # )
    # if total_data_sources_size == 0:
    #     return _stream_direct_llm_chat(session, response_id, query, user_name)
    #
    return _run_streaming_chat(
        session, response_id, query, query_configuration, user_name, crew_events_queue=crew_events_queue
    )


def _run_streaming_chat(session: Session, response_id: str, query: str, query_configuration: QueryConfiguration,
                        user_name: Optional[str],
                        crew_events_queue: queue.Queue) -> Generator[ChatResponse| str, None, None]:
    # if len(session.data_source_ids) != 1:
    #     raise HTTPException(
    #         status_code=400, detail="Only one datasource is supported for chat."
    #     )

    data_source_id: Optional[int] = session.data_source_ids[0] if session.data_source_ids else None
    streaming_thingee = querier.streaming_query(data_source_id, query, query_configuration,
                                              retrieve_chat_history(session.id), crew_events_queue=crew_events_queue)
    while True:
        try:
            yield next(streaming_thingee)
        except StopIteration as e:
            streaming_chat_response, condensed_question = e.value
            break
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

    if condensed_question and (condensed_question.strip() == query.strip()):
        condensed_question = None
    relevance, faithfulness = evaluators.evaluate_response(
        query, chat_response, session.inference_model
    )
    response_source_nodes = format_source_nodes(chat_response, data_source_id)
    new_chat_message = RagStudioChatMessage(
        id=response_id,
        session_id=session.id,
        source_nodes=response_source_nodes,
        inference_model=session.inference_model,
        rag_message=RagMessage(
            user=query,
            assistant=chat_response.response,
        ),
        evaluations=[
            Evaluation(name="relevance", value=relevance),
            Evaluation(name="faithfulness", value=faithfulness),
        ],
        timestamp=time.time(),
        condensed_question=condensed_question,
    )

    chat_history_manager.append_to_history(session.id, [new_chat_message])

    record_rag_mlflow_run(
        new_chat_message, query_configuration, response_id, session, user_name
    )


def _stream_direct_llm_chat(
    session: Session, response_id: str, query: str, user_name: Optional[str]
) -> Generator[ChatResponse, None, None]:
    record_direct_llm_mlflow_run(response_id, session, user_name)

    chat_response = llm_completion.stream_completion(
        session.id, query, session.inference_model
    )
    response: ChatResponse = ChatResponse(message=ChatMessage(content=query))
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
    chat_history_manager.append_to_history(session.id, [new_chat_message])
