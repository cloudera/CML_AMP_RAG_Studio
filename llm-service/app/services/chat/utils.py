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

from typing import List, Iterable

from llama_index.core.base.llms.types import MessageRole
from llama_index.core.chat_engine.types import AgentChatResponse
from pydantic import BaseModel

from app.services.chat_history.chat_history_manager import (
    get_chat_history_manager,
    RagPredictSourceNode,
)


class RagContext(BaseModel):
    role: MessageRole
    content: str


def retrieve_chat_history(session_id: int) -> List[RagContext]:
    chat_history = get_chat_history_manager().retrieve_chat_history(session_id)[-10:]
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
                dataSourceId=source_node.node.metadata["data_source_id"],
            )
        )
    response_source_nodes = sorted(
        response_source_nodes, key=lambda x: x.score, reverse=True
    )
    return response_source_nodes


def process_response(response: str | None) -> list[str]:
    if response is None:
        return []

    sentences: Iterable[str] = response.splitlines()
    sentences = map(lambda x: x.strip(), sentences)
    sentences = map(lambda x: x.removeprefix("*").strip(), sentences)
    sentences = map(lambda x: x.removeprefix("-").strip(), sentences)
    sentences = map(lambda x: x.strip("*"), sentences)
    sentences = filter(lambda x: len(x.split()) <= 60, sentences)
    sentences = filter(lambda x: x != "Empty Response", sentences)
    sentences = filter(lambda x: x != "", sentences)
    return list(sentences)[:5]
