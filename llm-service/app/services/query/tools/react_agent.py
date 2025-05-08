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
import asyncio
import logging
from functools import partial
from typing import Callable, Generator, AsyncGenerator

from llama_index.core.agent import ReActAgent, FunctionCallingAgent, AgentRunner
from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent, AgentStream
from llama_index.core.base.llms.types import ChatMessage, ChatResponse
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import AsyncBaseTool
from llama_index.core.workflow.handler import WorkflowHandler

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
) -> Callable[[str, list[ChatMessage]], StreamingAgentChatResponse]:
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
    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt="You are a helpful assistant with a set of tools to work from.",
        name="Assistant",
        description="A helpful assistant that can use tools to assist the user.",
    )

    workflow = AgentWorkflow(agents=[agent])

    def chat_stream_generator(
        message: str,
        chat_history: list[ChatMessage],
    ) -> Generator[ChatResponse, None, None]:

        resp = workflow.run(user_msg=message, chat_history=chat_history, memory=memory)

        for event in resp:
            yield ChatResponse(
                message=ChatMessage(content=event.response),
                delta=event.delta,
            )

        # This is a synchronous generator that yields ChatResponse objects
        # In a real implementation, you would use asyncio.run or similar to run the async code
        # For now, we'll create a generator that simulates the agent's output

        # First, yield an initial response
        # yield ChatResponse(message=ChatMessage(content=""), delta="")

        # Then yield responses based on the agent's processing
        # In a real implementation, this would be based on the events from handler.stream_events()
        # response_text = f"I'll help you with: {message}"
        # for word in response_text.split():
        #     yield ChatResponse(message=ChatMessage(content=word), delta=word + " ")

    def streaming_chat_response(
        message: str,
        chat_history: list[ChatMessage],
    ) -> StreamingAgentChatResponse:
        # Return a StreamingAgentChatResponse with chat_stream set to our generator
        return StreamingAgentChatResponse(
            chat_stream=chat_stream_generator(
                message=message, chat_history=chat_history
            )
        )

    return streaming_chat_response
