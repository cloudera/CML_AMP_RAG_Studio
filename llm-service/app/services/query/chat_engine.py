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
from typing import Any, Optional, List

from llama_index.core import Response, QueryBundle
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.callbacks import trace_method
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.chat_engine.types import AgentChatResponse
from llama_index.core.schema import NodeWithScore
from llama_index.core.tools import ToolOutput

from app.services import llm_completion
from app.services.query.query_configuration import QueryConfiguration

logger = logging.getLogger(__name__)


class FlexibleChatEngine(CondenseQuestionChatEngine):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._configuration: QueryConfiguration = QueryConfiguration()

    @property
    def configuration(self) -> QueryConfiguration:
        return self._configuration

    @configuration.setter
    def configuration(self, value: QueryConfiguration) -> None:
        self._configuration = value

    @trace_method("chat")
    def chat(
        self, message: str, chat_history: Optional[List[ChatMessage]] = None
    ) -> AgentChatResponse:
        message, query_response, tool_output = self.chat_internal(message, chat_history)

        # Record response
        self._memory.put(ChatMessage(role=MessageRole.USER, content=message))
        self._memory.put(
            ChatMessage(role=MessageRole.ASSISTANT, content=str(query_response))
        )

        return AgentChatResponse(response=str(query_response), sources=[tool_output])

    def retrieve(
        self, message: str, chat_history: Optional[List[ChatMessage]]
    ) -> List[NodeWithScore]:
        message, query_bundle = self._generate_query_message(message, chat_history)
        return self._query_engine.retrieve(query_bundle)

    def chat_internal(
        self, message: str, chat_history: Optional[List[ChatMessage]]
    ) -> tuple[str, Response, ToolOutput]:
        message, query_bundle = self._generate_query_message(message, chat_history)
        query_response: Response = self._query_engine.query(query_bundle)
        tool_output: ToolOutput = self._get_tool_output_from_response(
            message, query_response
        )
        return message, query_response, tool_output

    def _generate_query_message(
        self, message: str, chat_history: Optional[List[ChatMessage]]
    ) -> tuple[str, QueryBundle]:
        chat_history = chat_history or self._memory.get(input=message)
        if self.configuration.use_question_condensing:
            # Generate standalone question from conversation context and last message
            condensed_question = self._condense_question(chat_history, message)
            log_str = f"Querying with condensed question: {condensed_question}"
            logger.info(log_str)
            message = condensed_question
        embedding_strings = None
        if self.configuration.use_hyde:
            hypothetical = llm_completion.hypothetical(message, self.configuration)
            logger.info(f"hypothetical document: {hypothetical}")
            embedding_strings = [hypothetical]
        # Query with standalone question
        query_bundle = QueryBundle(message, custom_embedding_strs=embedding_strings)
        return message, query_bundle
