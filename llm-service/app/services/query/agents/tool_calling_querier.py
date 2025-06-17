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

from app.ai.indexing.summary_indexer import SummaryIndexer
from app.services.metadata_apis.session_metadata_api import Session
from app.services.query.agents.agent_tools.date import DateTool
from app.services.query.agents.agent_tools.mcp import get_llama_index_tools
from app.services.query.agents.agent_tools.retriever import (
    build_retriever_tool,
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
You are an expert agent that can answer questions with the help of tools. \
Go through the tools available and use them appropriately to answer the \
user's question. If you do not know the answer to a question, you \
truthfully say it does not know. As the agent, you will provide an \
answer based solely on the provided sources with citations to the \
paragraphs. 

Note for in-line citations:
* Use the citations from the chat history as is. 
* Use links provided by the tools if needed to answer the question and cite them in-line \
in the given format: the link should be in markdown format. For example: \
Refer to the example in [example.com](https://example.com). Do not make up links that are not \
present. 
* Cite from node_ids in the given format: the node_id \
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
    tools: list[BaseTool] = [DateTool()]
    if use_retrieval and chat_engine:
        retrieval_tool = build_retriever_tool(
            retriever=chat_engine.retriever,
            summaries=data_source_summaries,
            node_postprocessors=chat_engine.node_postprocessors,
        )
        tools.append(retrieval_tool)
    tools.extend(mcp_tools)

    gen, source_nodes = _run_streamer(chat_messages, enhanced_query, llm, tools)

    return StreamingAgentChatResponse(chat_stream=gen, source_nodes=source_nodes)


def _run_streamer(
    chat_messages: list[ChatMessage],
    enhanced_query: str,
    llm: FunctionCallingLLM,
    tools: list[BaseTool],
    verbose: bool = True,
) -> tuple[Generator[ChatResponse, None, None], list[NodeWithScore]]:
    agent = FunctionAgent(
        tools=cast(list[BaseTool | Callable[[], Any]], tools),
        llm=llm,
        system_prompt=DEFAULT_AGENT_PROMPT,
    )

    source_nodes = []

    async def agen() -> AsyncGenerator[ChatResponse, None]:
        handler = agent.run(user_msg=enhanced_query, chat_history=chat_messages)

        async for event in handler.stream_events():
            if isinstance(event, AgentSetup):
                data = f"Agent {event.current_agent_name} setup with input: {event.input[-1].content!s}"
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
                data = f"Agent {event.current_agent_name} started with input: {event.input[-1].content!s}"
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
                data = f"Agent {event.current_agent_name} response: {event.response!s}"
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
                    if verbose:
                        logger.info("=== Agent Stream with Tool Call ===")
                        logger.info(
                            f"Agent {event.current_agent_name} response: {event.response!s}"
                        )
                        logger.info("========================")
                    yield ChatResponse(
                        message=ChatMessage(
                            role=MessageRole.TOOL,
                            content=event.response,
                        ),
                        delta=event.delta,
                        raw=event.raw,
                        additional_kwargs={
                            "chat_event": ChatEvent(
                                type="agent_response",
                                name=event.current_agent_name,
                            ),
                        },
                    )
                elif event.response:
                    # Yield the delta response as a ChatResponse
                    yield ChatResponse(
                        message=ChatMessage(
                            role=MessageRole.ASSISTANT,
                            content="\n\n" + str(event.response),
                        ),
                        delta=event.delta,
                        raw=event.raw,
                    )
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
