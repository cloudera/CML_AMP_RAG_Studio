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
import datetime
import logging
import os
from typing import Optional, Generator, AsyncGenerator, Callable, cast, Any

import opik
from llama_index.core.agent.workflow import (
    FunctionAgent,
    AgentStream,
    ToolCall,
    ToolCallResult,
    AgentOutput,
    AgentInput,
    AgentSetup,
)
from llama_index.core.base.llms.types import ChatMessage, MessageRole, ChatResponse
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.schema import NodeWithScore
from llama_index.core.tools import BaseTool
from llama_index.core.workflow import StopEvent
from llama_index.llms.bedrock_converse import BedrockConverse
from llama_index.llms.bedrock_converse.utils import get_model_name

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.services.metadata_apis.session_metadata_api import Session
from app.services.models.providers import BedrockModelProvider
from app.services.query.agents.agent_tools.mcp import get_llama_index_tools
from app.services.query.agents.agent_tools.retriever import (
    build_retriever_tool,
)
from app.services.query.agents.non_streamer_bedrock_converse import (
    FakeStreamBedrockConverse,
)
from app.services.query.chat_engine import (
    FlexibleContextChatEngine,
)
from app.services.query.chat_events import ChatEvent

if os.environ.get("ENABLE_OPIK") == "True":
    opik.configure(
        use_local=True, url=os.environ.get("OPIK_URL", "http://localhost:5174")
    )

logger = logging.getLogger(__name__)

poison_pill = "poison_pill"

NON_SYSTEM_MESSAGE_MODELS = {
    "mistral.mistral-7b-instruct-v0:2",
    "mistral.mixtral-8x7b-instruct-v0:1",
}

BEDROCK_STREAMING_TOOL_MODELS = {
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-7-sonnet-20250219-v1:0",
    "anthropic.claude-sonnet-4-20250514-v1:0",
    "anthropic.claude-opus-4-20250514-v1:0",
    "amazon.nova-pro-v1:0",
    "cohere.command-r-plus-v1:0",
    "cohere.command-r-v1:0",
}


def should_use_retrieval(
    data_source_ids: list[int],
    exclude_knowledge_base: bool | None = None,
) -> tuple[bool, dict[int, str]]:
    if exclude_knowledge_base:
        return False, {}
    data_source_summaries: dict[int, str] = {}
    for data_source_id in data_source_ids:
        data_source_summary_indexer = SummaryIndexer.get_summary_indexer(data_source_id)
        if data_source_summary_indexer:
            data_source_summary = data_source_summary_indexer.get_full_summary()
            data_source_summaries[data_source_id] = data_source_summary
    return len(data_source_ids) > 0, data_source_summaries


DEFAULT_AGENT_PROMPT = """\
### DATE AND TIME
Today's date is {date} and the current time is {time}. This date and time \
is considered the current date and time for all responses. \

### ROLE DESCRIPTION
You are an expert agent that can answer questions with the help of tools. \
You will use the date and time provided above to answer questions \
to refine the user's query and provide the best possible answer. \

### BEST PRACTICES
You will follow these best practices when answering questions:
1. Refining the user's query according to the date \
and time provided above if necessary, and if the user 
has not provided enough information to answer the question. \
2. Going through the tools available.
3. Approaching the question step by step, using the tools 
available to you to gather information when necessary. 
4. Once you have the information you need, you will provide \
a final answer to the user with citations if available \
you used to answer the question.
5. If you do not know the answer to a question or cannot find the information \
you need to answer the question with the provided sources or tools, \
you truthfully say you do not know and let the user know how you arrived \
at the response and what information you used (links if any) to arrive \
at it and ask for clarification or more information. 

### OUTPUT FORMAT
As the agent, you will provide an answer based solely on the provided \
sources with citations (if available). Only return the answer with \
citations (if used) to the user. If you cannot answer the question with the \
provided sources or tools, you will return a message saying you \
cannot answer the question and ask the user to provide more \
information or clarify the question. \

### CITATION FORMAT
You will use the following format to cite sources in your response:
* Use the citations from the chat history as is.
* Use links provided by tool results if needed to answer the question and cite them in-line \
in the given format: the link should be in markdown format. For example: \
Refer to the example in [example.com](https://example.com). Do not make up links that are not \
present.
* Cite from tool results with node_ids in the given format: the node_id \
should be in an html anchor tag (<a href>) with an html 'class' of 'rag_citation'. \
Do not use filenames as citations. Only node ids should be used. \
For example: <a class="rag_citation" href="2" ></a>. Do not make up node ids that are not present 
in the context.
* All citations should be either in-line citations or markdown links.

For example:

<Contexts>
Source: 1
The sky is red in the evening and blue in the morning.

Source: 2
Water is wet when the sky is red.

Source: 3 
www.example1.com
The sky is red in the evening and blue in the morning.

Source: 4 
www.example2.com
Only in the evenings, is the water wet.

<Query>
When is water wet?

<Answer> 
Water will be wet when the sky is red<a class="rag_citation" href="1"></a> \
[example.com](www.example.com), which occurs in the evening. [example2](www.example2.com) <a class="rag_citation" href="2"></a>.
"""


def stream_chat(
    use_retrieval: bool,
    llm: FunctionCallingLLM,
    chat_engine: Optional[FlexibleContextChatEngine],
    enhanced_query: str,
    chat_messages: list[ChatMessage],
    session: Session,
    data_source_summaries: dict[int, str],
) -> StreamingAgentChatResponse:
    mcp_tools: list[BaseTool] = []
    if session.query_configuration and session.query_configuration.selected_tools:
        for tool_name in session.query_configuration.selected_tools:
            try:
                mcp_tools.extend(get_llama_index_tools(tool_name))
            except ValueError as e:
                logger.warning(f"Could not create adapter for tool {tool_name}: {e}")
                continue

    # Use the existing chat engine with the enhanced query for streaming response
    tools: list[BaseTool] = mcp_tools
    # Use tool calling only if retrieval is not the only tool to optimize performance
    if tools and use_retrieval and chat_engine:
        retrieval_tool = build_retriever_tool(
            retriever=chat_engine.retriever,
            summaries=data_source_summaries,
            node_postprocessors=chat_engine.node_postprocessors,
        )
        tools.insert(0, retrieval_tool)

    gen, source_nodes = _run_streamer(chat_messages, enhanced_query, llm, tools)

    return StreamingAgentChatResponse(chat_stream=gen, source_nodes=source_nodes)


def _run_streamer(
    chat_messages: list[ChatMessage],
    enhanced_query: str,
    llm: FunctionCallingLLM,
    tools: list[BaseTool],
    verbose: bool = True,
) -> tuple[Generator[ChatResponse, None, None], list[NodeWithScore]]:
    agent, enhanced_query = build_function_agent(enhanced_query, llm, tools)

    source_nodes: list[NodeWithScore] = []

    # If no tools are provided, we can directly stream the chat response
    if not tools:
        chat_gen = llm.stream_chat(
            messages=chat_messages
            + [ChatMessage(role=MessageRole.USER, content=enhanced_query)]
        )
        return chat_gen, source_nodes

    async def agen() -> AsyncGenerator[ChatResponse, None]:
        handler = agent.run(user_msg=enhanced_query, chat_history=chat_messages)

        async for event in handler.stream_events():
            if isinstance(event, AgentSetup):
                data = f"{event.current_agent_name} setup with input: {event.input[-1].content!s}"
                if verbose:
                    logger.info("=== Agent Setup ===")
                    logger.info(data)
                    logger.info("========================")
                yield ChatResponse(
                    message=ChatMessage(
                        role=MessageRole.FUNCTION,
                        content="",
                    ),
                    delta="",
                    raw="",
                    additional_kwargs={
                        "chat_event": ChatEvent(
                            type="agent_setup",
                            name=event.current_agent_name,
                            data=data,
                        ),
                    },
                )
            elif isinstance(event, AgentInput):
                data = f"{event.current_agent_name} started with input: {event.input[-1].content!s}"
                if verbose:
                    logger.info("=== Agent Input ===")
                    logger.info(data)
                    logger.info("========================")
                yield ChatResponse(
                    message=ChatMessage(
                        role=MessageRole.FUNCTION,
                        content="",
                    ),
                    delta="",
                    raw="",
                    additional_kwargs={
                        "chat_event": ChatEvent(
                            type="agent_input",
                            name=event.current_agent_name,
                            data=data,
                        ),
                    },
                )
            elif isinstance(event, ToolCall) and not isinstance(event, ToolCallResult):
                data = f"Calling function: {event.tool_name} with args: {event.tool_kwargs}"
                if verbose:
                    logger.info("=== Calling Function ===")
                    logger.info(data)
                yield ChatResponse(
                    message=ChatMessage(
                        role=MessageRole.TOOL,
                        content="",
                    ),
                    delta="",
                    raw="",
                    additional_kwargs={
                        "chat_event": ChatEvent(
                            type="tool_call", name=event.tool_name, data=data
                        ),
                    },
                )
            elif isinstance(event, ToolCallResult):
                data = f"Got output: {event.tool_output!s}"
                if verbose:
                    logger.info(data)
                    logger.info("========================")
                if (
                    event.tool_output.raw_output
                    and isinstance(event.tool_output.raw_output, list)
                    and all(
                        isinstance(elem, NodeWithScore)
                        for elem in event.tool_output.raw_output
                    )
                ):
                    source_nodes.extend(event.tool_output.raw_output)
                yield ChatResponse(
                    message=ChatMessage(
                        role=MessageRole.TOOL,
                        content="",
                    ),
                    delta="",
                    raw="",
                    additional_kwargs={
                        "chat_event": ChatEvent(
                            type="tool_result",
                            name=event.tool_name,
                            data=data,
                        ),
                    },
                )
            elif isinstance(event, AgentOutput):
                data = f"{event.current_agent_name} response: {event.response!s}"
                if verbose:
                    logger.info("=== LLM Response ===")
                    logger.info(
                        f"{str(event.response) if event.response else 'No content'}"
                    )
                    logger.info("========================")
                yield ChatResponse(
                    message=ChatMessage(
                        role=MessageRole.TOOL,
                        content=(
                            event.response.content if event.response.content else ""
                        ),
                    ),
                    delta="",
                    raw=event.raw,
                    additional_kwargs={
                        "chat_event": ChatEvent(
                            type="agent_response",
                            name=event.current_agent_name,
                            data=data,
                        ),
                    },
                )
            elif isinstance(event, AgentStream):
                if len(event.tool_calls) > 0:
                    continue
                else:
                    delta = event.delta or ""

                    # if delta is empty and response is empty,
                    # it is a start to a tool call stream
                    if BedrockModelProvider.is_enabled():
                        delta = event.delta or ""
                        if "contentBlockStart" in event.raw:
                            # check the contentBlockIndex in the raw response
                            if event.raw["contentBlockStart"]["contentBlockIndex"]:
                                # If contentBlockIndex is > 0, prepend a newline to the delta
                                delta = "\n\n" + delta

                    # Yield the delta response as a ChatResponse
                    yield ChatResponse(
                        message=ChatMessage(
                            role=MessageRole.ASSISTANT,
                            content=event.response,
                        ),
                        delta=delta,
                        raw=event.raw,
                    )
            elif isinstance(event, StopEvent):
                pass
            else:
                logger.info(f"Unhandled event of type: {type(event)}: {event}")

        await handler
        if e := handler.exception():
            raise e
        if handler.ctx:
            await handler.ctx.shutdown()

    def gen() -> Generator[ChatResponse, None, None]:
        loop = asyncio.new_event_loop()
        astream = agen()
        try:
            while True:
                item = loop.run_until_complete(anext(astream))
                yield item
        except (StopAsyncIteration, GeneratorExit):
            pass
        finally:
            try:
                loop.run_until_complete(astream.aclose())
            except Exception as e:
                logger.warning(f"Exception during async generator close: {e}")
            if not loop.is_closed():
                loop.stop()
                loop.close()

    return gen(), source_nodes


def build_function_agent(
    enhanced_query: str, llm: FunctionCallingLLM, tools: list[BaseTool]
) -> tuple[FunctionAgent, str]:
    formatted_prompt = DEFAULT_AGENT_PROMPT.format(
        date=datetime.datetime.now().strftime("%A, %B %d, %Y"),
        time=datetime.datetime.now().strftime("%H:%M:%S %p"),
    )
    callable_tools = cast(list[BaseTool | Callable[[], Any]], tools)
    if llm.metadata.model_name in NON_SYSTEM_MESSAGE_MODELS:
        agent = FunctionAgent(tools=callable_tools, llm=llm)
        enhanced_query = (
            "ROLE DESCRIPTION =========================================\n"
            + formatted_prompt
            + "=========================================================\n"
            "USER QUERY ==============================================\n"
            + enhanced_query
        )
    else:
        if (
            isinstance(llm, BedrockConverse)
            and get_model_name(llm.metadata.model_name)
            not in BEDROCK_STREAMING_TOOL_MODELS
        ):
            llm = FakeStreamBedrockConverse.from_bedrock_converse(llm)
        agent = FunctionAgent(
            tools=callable_tools, llm=llm, system_prompt=formatted_prompt
        )

    return agent, enhanced_query
