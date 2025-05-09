#
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
import logging
from typing import Any, Optional, List, Tuple

from llama_index.core import VectorStoreIndex, PromptTemplate
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine import (
    CondensePlusContextChatEngine,
)
from llama_index.core.llms import LLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.response_synthesizers import CompactAndRefine
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.tools import ToolOutput

from .flexible_retriever import FlexibleRetriever
from .query_configuration import QueryConfiguration
from .simple_reranker import SimpleReranker
from .. import llm_completion, models
from ..metadata_apis.data_sources_metadata_api import get_metadata

logger = logging.getLogger(__name__)

CUSTOM_TEMPLATE = """\
Given a conversation (between Human and Assistant) and a follow up message from Human, \
rewrite the message to be a standalone question that captures all relevant context \
from the conversation. Just provide the question, not any description of it.

<Chat History>
{chat_history}

<Follow Up Message>
{question}

<Standalone question>
"""

CUSTOM_PROMPT = PromptTemplate(CUSTOM_TEMPLATE)


class FlexibleContextChatEngine(CondensePlusContextChatEngine):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._configuration: QueryConfiguration = QueryConfiguration()

    def condense_question(
        self, chat_history: List[ChatMessage], latest_message: str
    ) -> str:
        return super()._condense_question(chat_history, latest_message)

    def _run_c3(
        self,
        message: str,
        chat_history: Optional[List[ChatMessage]] = None,
        streaming: bool = False,
    ) -> Tuple[CompactAndRefine, ToolOutput, List[NodeWithScore]]:
        if chat_history is not None:
            self._memory.set(chat_history)

        chat_history = self._memory.get(input=message)

        # Condense conversation history and latest message to a standalone question
        vector_match_input = message
        if self._configuration.use_question_condensing:
            vector_match_input = self._condense_question(chat_history, message)
            if self._verbose:
                logger.info(f"Condensed question: {vector_match_input}")

        # get the context nodes using the condensed question
        if self._configuration.use_hyde:
            vector_match_input = llm_completion.hypothetical(
                vector_match_input, self._configuration
            )
            if self._verbose:
                logger.info(f"Hypothetical document: {vector_match_input}")

        context_nodes = self._get_nodes(vector_match_input)
        context_source = ToolOutput(
            tool_name="retriever",
            content=str(context_nodes),
            raw_input={"message": vector_match_input},
            raw_output=context_nodes,
        )

        # build the response synthesizer
        response_synthesizer = self._get_response_synthesizer(
            chat_history, streaming=streaming
        )

        return response_synthesizer, context_source, context_nodes


def build_flexible_chat_engine(
    configuration: QueryConfiguration,
    llm: LLM,
    embedding_model: BaseEmbedding,
    index: VectorStoreIndex,
    data_source_id: int,
) -> FlexibleContextChatEngine:
    retriever = FlexibleRetriever(configuration, index, embedding_model, data_source_id, llm)
    postprocessors = _create_node_postprocessors(
        configuration, data_source_id=data_source_id
    )
    chat_engine: FlexibleContextChatEngine = FlexibleContextChatEngine.from_defaults(
        llm=llm,
        condense_question_prompt=CUSTOM_PROMPT,
        retriever=retriever,
        node_postprocessors=postprocessors,
    )
    chat_engine._configuration = configuration
    return chat_engine


class DebugNodePostProcessor(BaseNodePostprocessor):
    def _postprocess_nodes(
        self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle] = None
    ) -> list[NodeWithScore]:
        logger.debug(f"nodes: {len(nodes)}")
        for node in sorted(nodes, key=lambda n: n.node.node_id):
            logger.debug(
                node.node.node_id, node.node.metadata["document_id"], node.score
            )

        return nodes


def _create_node_postprocessors(
    configuration: QueryConfiguration,
    data_source_id: int,
) -> list[BaseNodePostprocessor]:
    if not configuration.use_postprocessor:
        return []

    data_source = get_metadata(data_source_id=data_source_id)
    if data_source.summarization_model is None:
        return [SimpleReranker(top_n=configuration.top_k)]

    return [
        DebugNodePostProcessor(),
        models.Reranking.get(
            model_name=configuration.rerank_model_name,
            top_n=configuration.top_k,
        )
        or SimpleReranker(top_n=configuration.top_k),
        DebugNodePostProcessor(),
    ]
