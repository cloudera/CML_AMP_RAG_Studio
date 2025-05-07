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
from typing import Optional

from fastapi import HTTPException

from app.services import evaluators, llm_completion
from app.services.chat.utils import retrieve_chat_history, format_source_nodes
from app.services.chat_history.chat_history_manager import (
    Evaluation,
    RagMessage,
    RagStudioChatMessage,
    chat_history_manager,
)
from app.services.metadata_apis.session_metadata_api import Session
from app.services.mlflow import record_rag_mlflow_run, record_direct_llm_mlflow_run
from app.services.query import querier
from app.services.query.query_configuration import QueryConfiguration
from app.ai.vector_stores.vector_store_factory import VectorStoreFactory
from app.rag_types import RagPredictConfiguration


def chat(
    session: Session,
    query: str,
    configuration: RagPredictConfiguration,
    user_name: Optional[str],
) -> RagStudioChatMessage:
    query_configuration = QueryConfiguration(
        top_k=session.response_chunks,
        model_name=session.inference_model,
        rerank_model_name=session.rerank_model,
        exclude_knowledge_base=configuration.exclude_knowledge_base,
        use_question_condensing=configuration.use_question_condensing,
        use_hyde=session.query_configuration.enable_hyde,
        use_summary_filter=session.query_configuration.enable_summary_filter,
    )

    response_id = str(uuid.uuid4())

    if configuration.exclude_knowledge_base or len(session.data_source_ids) == 0:
        return direct_llm_chat(session, response_id, query, user_name)

    total_data_sources_size: int = sum(
        map(
            lambda ds_id: VectorStoreFactory.for_chunks(ds_id).size() or 0,
            session.data_source_ids,
        )
    )
    if total_data_sources_size == 0:
        return direct_llm_chat(session, response_id, query, user_name)

    new_chat_message: RagStudioChatMessage = _run_chat(
        session, response_id, query, query_configuration, user_name
    )

    chat_history_manager.append_to_history(session.id, [new_chat_message])
    return new_chat_message


def _run_chat(
    session: Session,
    response_id: str,
    query: str,
    query_configuration: QueryConfiguration,
    user_name: Optional[str],
) -> RagStudioChatMessage:
    if len(session.data_source_ids) != 1:
        raise HTTPException(
            status_code=400, detail="Only one datasource is supported for chat."
        )

    data_source_id: int = session.data_source_ids[0]
    response, condensed_question = querier.query(
        data_source_id,
        query,
        query_configuration,
        retrieve_chat_history(session.id),
    )
    if condensed_question and (condensed_question.strip() == query.strip()):
        condensed_question = None
    relevance, faithfulness = evaluators.evaluate_response(
        query, response, session.inference_model
    )
    response_source_nodes = format_source_nodes(response, data_source_id)
    new_chat_message = RagStudioChatMessage(
        id=response_id,
        session_id=session.id,
        source_nodes=response_source_nodes,
        inference_model=session.inference_model,
        rag_message=RagMessage(
            user=query,
            assistant=response.response,
        ),
        evaluations=[
            Evaluation(name="relevance", value=relevance),
            Evaluation(name="faithfulness", value=faithfulness),
        ],
        timestamp=time.time(),
        condensed_question=condensed_question,
    )

    record_rag_mlflow_run(
        new_chat_message, query_configuration, response_id, session, user_name
    )
    return new_chat_message


def direct_llm_chat(
    session: Session, response_id: str, query: str, user_name: Optional[str]
) -> RagStudioChatMessage:
    record_direct_llm_mlflow_run(response_id, session, user_name)

    chat_response = llm_completion.completion(
        session.id, query, session.inference_model
    )
    new_chat_message = RagStudioChatMessage(
        id=response_id,
        session_id=session.id,
        source_nodes=[],
        inference_model=session.inference_model,
        evaluations=[],
        rag_message=RagMessage(
            user=query,
            assistant=str(chat_response.message.content),
        ),
        timestamp=time.time(),
        condensed_question=None,
    )
    chat_history_manager.append_to_history(session.id, [new_chat_message])
    return new_chat_message


