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

from llama_index.core.base.llms.types import MessageRole

from ..rag_types import RagPredictConfiguration
from . import evaluators, qdrant
from .chat_store import (
    Evaluation,
    RagContext,
    RagPredictSourceNode,
    RagStudioChatMessage,
    chat_store,
)


def v2_chat(
    session_id: int,
    data_source_id: int,
    query: str,
    configuration: RagPredictConfiguration,
) -> RagStudioChatMessage:
    response_id = str(uuid.uuid4())
    if qdrant.size_of(data_source_id) == 0:
        return RagStudioChatMessage(
            id=response_id,
            source_nodes=[],
            rag_message={
                "user": query,
                "assistant": "I don't have any documents to answer your question.",
            },
            evaluations=[],
            timestamp=time.time(),
        )

    response = qdrant.query(
        data_source_id,
        query,
        configuration,
        retrieve_chat_history(session_id),
    )
    relevance, faithfulness = evaluators.evaluate_response(query, response)
    response_source_nodes = format_source_nodes(response)
    new_chat_message = RagStudioChatMessage(
        id=response_id,
        source_nodes=response_source_nodes,
        rag_message={
            "user": query,
            "assistant": response.response,
        },
        evaluations=[
            Evaluation(name="relevance", value=relevance),
            Evaluation(name="faithfulness", value=faithfulness),
        ],
        timestamp=time.time(),
    )
    chat_store.append_to_history(session_id, [new_chat_message])
    return new_chat_message


def retrieve_chat_history(session_id):
    chat_history = chat_store.retrieve_chat_history(session_id)[:10]
    history: [RagContext] = list()
    for message in chat_history:
        history.append(
            RagContext(role=MessageRole.USER, content=message.rag_message["user"])
        )
        history.append(
            RagContext(
                role=MessageRole.ASSISTANT, content=message.rag_message["assistant"]
            )
        )
    return history


def format_source_nodes(response):
    response_source_nodes = []
    for source_node in response.source_nodes:
        source_metadata = source_node.node.metadata
        doc_id = source_metadata.get("document_id", source_node.node.node_id)
        if "original_filename" in source_metadata:
            source_file_name = source_metadata["original_filename"]
        else:
            source_file_name = source_metadata["file_name"]
        response_source_nodes.append(
            RagPredictSourceNode(
                node_id=source_node.node.node_id,
                doc_id=doc_id,
                source_file_name=source_file_name,
                score=source_node.score,
            )
        )
    response_source_nodes = sorted(
        response_source_nodes, key=lambda x: x.score, reverse=True
    )
    return response_source_nodes


def generate_suggested_questions(
    configuration, data_source_id, data_source_size, session_id
):
    chat_history = retrieve_chat_history(session_id)
    if data_source_size == 0:
        suggested_questions = []
    else:
        query_str = (
            "Give me a list of questions that you can answer."
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
        response = qdrant.query(
            data_source_id,
            query_str,
            configuration,
            [],
        )

        suggested_questions = process_response(response.response)
    return suggested_questions


def process_response(response: str | None) -> list[str]:
    if response is None:
        return []

    sentences = response.split("*")
    sentences = filter(lambda x: len(x.split()) <= 15, sentences)
    sentences = map(lambda x: x.strip(), sentences)
    sentences = filter(lambda x: x != "Empty Response", sentences)
    sentences = filter(lambda x: x != "", sentences)
    return list(sentences)[:5]
