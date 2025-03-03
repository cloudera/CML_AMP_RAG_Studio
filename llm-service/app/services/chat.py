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
import asyncio
import time
import uuid
from typing import List, Iterable

from fastapi import HTTPException
from llama_index.core.base.llms.types import MessageRole
from llama_index.core.chat_engine.types import AgentChatResponse

from . import evaluators, llm_completion
from .chat_store import (
    ChatHistoryManager,
    Evaluation,
    RagContext,
    RagPredictSourceNode,
    RagStudioChatMessage,
    RagMessage,
)
from .metadata_apis import session_metadata_api
from .metadata_apis.session_metadata_api import Session
from .mlflow import record_rag_mlflow_run, record_direct_llm_mlflow_run
from .query import querier
from .query.query_configuration import QueryConfiguration
from ..ai.vector_stores.qdrant import QdrantVectorStore
from ..rag_types import RagPredictConfiguration


def v2_chat(
    session_id: int, query: str, configuration: RagPredictConfiguration, user_name: str
) -> RagStudioChatMessage:
    session = session_metadata_api.get_session(session_id)
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

    new_chat_message: RagStudioChatMessage = _run_chat(
        session, response_id, query, query_configuration, user_name
    )

    ChatHistoryManager().append_to_history(session_id, [new_chat_message])
    return new_chat_message


def _run_chat(
    session: Session,
    response_id: str,
    query: str,
    query_configuration: QueryConfiguration,
    user_name: str,
) -> RagStudioChatMessage:
    if len(session.data_source_ids) != 1:
        raise HTTPException(
            status_code=400, detail="Only one datasource is supported for chat."
        )

    data_source_id: int = session.data_source_ids[0]
    if QdrantVectorStore.for_chunks(data_source_id).size() == 0:
        return RagStudioChatMessage(
            id=response_id,
            source_nodes=[],
            inference_model=None,
            rag_message=RagMessage(
                user=query,
                assistant="I don't have any documents to answer your question.",
            ),
            evaluations=[],
            timestamp=time.time(),
            condensed_question=None,
        )
    response, condensed_question = querier.query(
        data_source_id,
        query,
        query_configuration,
        retrieve_chat_history(session.id),
    )
    if condensed_question and (condensed_question.strip() == query.strip()):
        condensed_question = None
    relevance, faithfulness = asyncio.run(evaluators.evaluate_response(
        query, response, session.inference_model
    ))
    response_source_nodes = format_source_nodes(response)
    new_chat_message = RagStudioChatMessage(
        id=response_id,
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


def retrieve_chat_history(session_id: int) -> List[RagContext]:
    chat_history = ChatHistoryManager().retrieve_chat_history(session_id)[:10]
    history: List[RagContext] = []
    for message in chat_history:
        history.append(
            RagContext(role=MessageRole.USER, content=message.rag_message.user)
        )
        history.append(
            RagContext(
                role=MessageRole.ASSISTANT, content=message.rag_message.assistant
            )
        )
    return history


def format_source_nodes(response: AgentChatResponse) -> List[RagPredictSourceNode]:
    response_source_nodes = []
    for source_node in response.source_nodes:
        doc_id = source_node.node.metadata.get("document_id", source_node.node.node_id)
        response_source_nodes.append(
            RagPredictSourceNode(
                node_id=source_node.node.node_id,
                doc_id=doc_id,
                source_file_name=source_node.node.metadata["file_name"],
                score=source_node.score or 0.0,
            )
        )
    response_source_nodes = sorted(
        response_source_nodes, key=lambda x: x.score, reverse=True
    )
    return response_source_nodes


def generate_suggested_questions(
    session_id: int,
) -> List[str]:
    session = session_metadata_api.get_session(session_id)
    if len(session.data_source_ids) != 1:
        raise HTTPException(
            status_code=400,
            detail="Only one datasource is supported for question suggestion.",
        )
    data_source_id = session.data_source_ids[0]

    total_data_sources_size: int = sum(
        map(
            lambda ds_id: QdrantVectorStore.for_chunks(ds_id).size() or 0,
            session.data_source_ids,
        )
    )
    if total_data_sources_size == 0:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    chat_history = retrieve_chat_history(session_id)
    if total_data_sources_size == 0:
        suggested_questions = []
    else:
        query_str = (
            "Give me a list of questions that you can answer."
            " Each question should be on a new line."
            " There should be no more than four (4) questions."
            " Each question should be no longer than fifteen (15) words."
            " The response should be a bulleted list, using an asterisk (*) to denote the bullet item."
            " Do not return questions based on the metadata of the document. Only the content."
            " Do not start like this - `Here are four questions that I can answer based on the context information`"
            " Only return the list."
        )
        if chat_history:
            query_str = (
                query_str
                + (
                    "I will provide a response from my last question to help with generating new questions."
                    " Consider returning questions that are relevant to the response"
                    " They might be follow up questions or questions that are related to the response."
                    " Here is the last response received:\n"
                )
                + chat_history[-1].content
            )
        response, _ = querier.query(
            data_source_id,
            query_str,
            QueryConfiguration(
                top_k=session.response_chunks,
                model_name=session.inference_model,
                rerank_model_name=None,
                exclude_knowledge_base=False,
                use_question_condensing=False,
                use_hyde=False,
                use_postprocessor=False,
            ),
            [],
        )

        suggested_questions = process_response(response.response)
    return suggested_questions


def process_response(response: str | None) -> list[str]:
    if response is None:
        return []

    sentences: Iterable[str] = response.splitlines()
    sentences = map(lambda x: x.strip(), sentences)
    sentences = map(lambda x: x.removeprefix("*").strip(), sentences)
    sentences = map(lambda x: x.removeprefix("-").strip(), sentences)
    sentences = map(lambda x: x.strip("*"), sentences)
    sentences = filter(lambda x: len(x.split()) <= 15, sentences)
    sentences = filter(lambda x: x != "Empty Response", sentences)
    sentences = filter(lambda x: x != "", sentences)
    return list(sentences)[:5]


def direct_llm_chat(
    session_id: int, query: str, user_name: str
) -> RagStudioChatMessage:
    session = session_metadata_api.get_session(session_id)
    response_id = str(uuid.uuid4())
    record_direct_llm_mlflow_run(response_id, session, user_name)

    chat_response = llm_completion.completion(
        session_id, query, session.inference_model
    )
    new_chat_message = RagStudioChatMessage(
        id=response_id,
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
    ChatHistoryManager().append_to_history(session_id, [new_chat_message])
    return new_chat_message
