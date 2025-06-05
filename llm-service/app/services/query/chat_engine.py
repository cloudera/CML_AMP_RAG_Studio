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

from llama_index.core import PromptTemplate
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine import (
    CondensePlusContextChatEngine,
)
from llama_index.core.llms import LLM
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.response_synthesizers import CompactAndRefine
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.tools import ToolOutput

from .query_configuration import QueryConfiguration
from .simple_reranker import SimpleReranker
from .. import llm_completion, models

logger = logging.getLogger(__name__)

CUSTOM_CONTEXT_PROMPT_TEMPLATE = """\
The following is a friendly conversation between a user and an AI assistant. \
The assistant is talkative and provides lots of specific details from its context. \
If the assistant does not know the answer to a question, it truthfully says it \
does not know. 

As the assistant, please provide an answer based solely on the provided sources with \
citations to the paragraphs. When referencing information from a source, \
cite the appropriate source(s) using their corresponding ids. \
Every answer/paragraph should include at least one source citation. \
Only cite a source when you are explicitly referencing it. \
The citations should be the href of an anchor tag (<a class="rag_citation" href=CITATION_HERE></a>), \
and (IMPORTANT) in-line with the text. No footnotes or endnotes. \
If none of the sources are helpful, you should indicate that. \
Do not make up source ids for citations. Only use the source ids \
provided in the contexts. \
For example:

<Contexts>
Source: 1
The sky is red in the evening and blue in the morning.

Source: 2
Water is wet when the sky is red.

<Query>
When is water wet?

<Answer>
Water will be wet when the sky is red<a class="rag_citation" href="1"></a>, \
which occurs in the evening<a class="rag_citation" href="2"></a>.

Now it's your turn. Below are several numbered sources of information:

<Contexts>
{context_str}

<Query>
{query_str}

<Answer>
"""


CUSTOM_CONTEXT_REFINE_PROMPT_TEMPLATE = """\
The following is a friendly conversation between a user and an AI assistant. \
The assistant is talkative and provides lots of specific details from its context. \
If the assistant does not know the answer to a question, it truthfully says \
it does not know.

As the assistant, please provide an answer based solely on the provided sources with \
citations to the paragraphs. When referencing information from a source, \
cite the appropriate source(s) using their corresponding ids. \
Every answer/paragraph should include at least one source citation. \
Only cite a source when you are explicitly referencing it. \
The citations should be the href of an anchor tag (<a class="rag_citation" href=CITATION_HERE></a>), \
and (IMPORTANT) in-line with the text. No footnotes or endnotes. \
If none of the sources are helpful, you should indicate that. \
Do not make up source ids for citations. Only use the source ids \
provided in the contexts. \
For example:

<Contexts>
Source: 1
The sky is red in the evening and blue in the morning.

Source: 2
Water is wet when the sky is red.

<Query>
When is water wet?

<Answer> 
Water will be wet when the sky is red<a class="rag_citation" href="1"></a>, \
which occurs in the evening<a class="rag_citation" href="2"></a>.

Now it's your turn. We have provided an existing answer: 

<Existing Answer>
{existing_answer}

Below are several numbered sources of information.
Use them to refine the existing answer.
If the provided sources are not helpful, you will repeat the existing answer.
Begin refining!

<Contexts>
{context_msg}

<Query>
{query_str}

<Answer>
"""

CUSTOM_CONDENSE_TEMPLATE = """\
Given a conversation (between Human and Assistant) and a follow up message from Human, \
rewrite the message to be a standalone question that captures all relevant context \
from the conversation. Just provide the question, not any description of it.

<Chat History>
{chat_history}

<Follow Up Message>
{question}

<Standalone question>
"""

CUSTOM_CONDENSE_PROMPT = PromptTemplate(CUSTOM_CONDENSE_TEMPLATE)
CUSTOM_CONTEXT_PROMPT = PromptTemplate(CUSTOM_CONTEXT_PROMPT_TEMPLATE)
CUSTOM_CONTEXT_REFINE_PROMPT = PromptTemplate(CUSTOM_CONTEXT_REFINE_PROMPT_TEMPLATE)


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
        for node in context_nodes:
            # number the nodes in the content
            new_content = f"Source: {node.node.node_id}\n{node.node.get_content()}\n"
            node.node.set_content(value=new_content)
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
    retriever: Optional[BaseRetriever],
) -> Optional[FlexibleContextChatEngine]:
    if not retriever:
        return None
    postprocessors = _create_node_postprocessors(configuration)
    chat_engine: FlexibleContextChatEngine = FlexibleContextChatEngine.from_defaults(
        llm=llm,
        context_prompt=CUSTOM_CONTEXT_PROMPT,
        context_refine_prompt=CUSTOM_CONTEXT_REFINE_PROMPT,
        condense_prompt=CUSTOM_CONDENSE_PROMPT,
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
) -> list[BaseNodePostprocessor]:
    if not configuration.use_postprocessor:
        return []

    if configuration.rerank_model_name is None:
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
