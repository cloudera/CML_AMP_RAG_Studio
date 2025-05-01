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

import logging

from llama_index.core.agent import ReActAgent, FunctionCallingAgent, AgentRunner
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import AsyncBaseTool

from app.services import models
from app.services.query.chat_engine import FlexibleContextChatEngine
from app.services.query.query_configuration import QueryConfiguration
from app.services.query.tools.direct_llm_chat_tool import direct_llm_chat_tool
from app.services.query.tools.multiplier_tool import multiplier_tool

from app.services.query.tools.query_engine_tool import query_engine_tool
from app.services.query.tools.date_tool import current_date_tool

logger = logging.getLogger(__name__)


def configure_agent_runner(
    chat_messages: list[ChatMessage],
    configuration: QueryConfiguration,
    chat_engine: FlexibleContextChatEngine | None,
    data_source_id: int | None,
) -> AgentRunner:
    llm = models.LLM.get(model_name=configuration.model_name)

    tools: list[AsyncBaseTool] = []
    tools.append(direct_llm_chat_tool(chat_messages, llm))
    # Create a retriever tool
    if chat_engine is not None and data_source_id is not None:
        tools.append(
            query_engine_tool(chat_messages, chat_engine, data_source_id=data_source_id)
        )
    tools.append(multiplier_tool())
    tools.append(current_date_tool())

    memory = ChatMemoryBuffer.from_defaults(
        token_limit=40000, chat_history=chat_messages
    )
    agent = FunctionCallingAgent.from_tools(tools=tools, llm=llm, verbose=True, memory=memory)

    return agent
