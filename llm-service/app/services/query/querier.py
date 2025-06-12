# ##############################################################################
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. (“Cloudera”) to the
#  contrary, (A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
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
from __future__ import annotations

import json
import os
import re
from copy import copy
from queue import Queue
from typing import Optional, TYPE_CHECKING, cast

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.schema import NodeWithScore
from llama_index.core.tools import BaseTool as LLamaTool
from llama_index.core.tools import FunctionTool

from .agents.tool_calling_querier import (
    should_use_retrieval,
    stream_chat,
    poison_pill,
)
from .chat_events import ToolEvent
from .flexible_retriever import FlexibleRetriever
from .multi_retriever import MultiSourceRetriever
from ..metadata_apis.session_metadata_api import Session
from ...config import settings

if TYPE_CHECKING:
    from ..chat.utils import RagContext

import logging

import botocore.exceptions
from fastapi import HTTPException
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.chat_engine.types import (
    AgentChatResponse,
    StreamingAgentChatResponse,
)
from llama_index.core.indices import VectorStoreIndex

from app.services import models
from app.services.query.query_configuration import QueryConfiguration
from .chat_engine import build_flexible_chat_engine, FlexibleContextChatEngine
from ...ai.vector_stores.vector_store_factory import VectorStoreFactory
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

logger = logging.getLogger(__name__)


def get_llama_index_tools(server_name: str) -> list[FunctionTool]:
    """
    Find an MCP server by name in the mcp.json file and return the appropriate adapter.

    Args:
        server_name: The name of the MCP server to find

    Returns:
        An MCPServerAdapter configured for the specified server

    Raises:
        ValueError: If the server name is not found in the mcp.json file
    """
    mcp_json_path = os.path.join(settings.tools_dir, "mcp.json")

    with open(mcp_json_path, "r") as f:
        mcp_config = json.load(f)

    mcp_servers = mcp_config["mcp_servers"]
    server_config = next(filter(lambda x: x["name"] == server_name, mcp_servers), None)

    if server_config:
        environment: dict[str, str] | None = copy(dict(os.environ))
        if "env" in server_config and environment:
            environment.update(server_config["env"])

        if "command" in server_config:
            client = BasicMCPClient(
                command_or_url=server_config["command"],
                args=server_config.get("args", []),
                env=environment,
            )
        elif "url" in server_config:
            client = BasicMCPClient(command_or_url=server_config["url"])
        else:
            raise ValueError("Not configured right...fixme")
        tool_spec = McpToolSpec(client=client)
        return tool_spec.to_tool_list()

    raise ValueError(f"Invalid configuration for MCP server '{server_name}'")


def streaming_query(
    chat_engine: Optional[FlexibleContextChatEngine],
    query_str: str,
    configuration: QueryConfiguration,
    chat_messages: list[ChatMessage],
    tool_events_queue: Queue[ToolEvent],
    session: Session,
) -> StreamingAgentChatResponse:
    all_tools: list[LLamaTool] = []

    if session.query_configuration and session.query_configuration.selected_tools:
        for tool_name in session.query_configuration.selected_tools:
            try:
                llama_tools = get_llama_index_tools(tool_name)
                # print(
                #     f"Adding adapter for tools: {[tool.name for tool in adapter.tools]}"
                # )
                all_tools.extend(llama_tools)
            except ValueError as e:
                logger.warning(f"Could not create adapter for tool {tool_name}: {e}")
                continue

    llm = models.LLM.get(model_name=configuration.model_name)

    chat_response: StreamingAgentChatResponse
    if configuration.use_tool_calling and llm.metadata.is_function_calling_model:
        use_retrieval, data_source_summaries = should_use_retrieval(
            session.data_source_ids, configuration.exclude_knowledge_base
        )

        chat_response = stream_chat(
            use_retrieval,
            cast(FunctionCallingLLM, llm),
            chat_engine,
            query_str,
            chat_messages,
            all_tools,
            data_source_summaries,
        )
        tool_events_queue.put(ToolEvent(type=poison_pill, name="no-op"))
        return chat_response
    if not chat_engine:
        raise HTTPException(
            status_code=500,
            detail="Chat engine is not initialized. Please check the configuration.",
        )

    try:
        chat_response = chat_engine.stream_chat(query_str, chat_messages)
        tool_events_queue.put(ToolEvent(type=poison_pill, name="no-op"))
        logger.debug("query response received from chat engine")
    except botocore.exceptions.ClientError as error:
        logger.warning(error.response)
        json_error = error.response
        raise HTTPException(
            status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
            detail=json_error["StatusReason"],
        ) from error

    return chat_response


def get_nodes_from_output(
    output: str,
    session: Session,
) -> list[NodeWithScore]:
    source_node_ids_w_score: dict[str, float] = {}

    # Extract the node ids from string output
    extracted_node_ids = re.findall(
        r"<a class=\"rag_citation\" href=\"(.*?)\">",
        output,
    )

    # add the extracted node ids to the source node ids
    for node_id in extracted_node_ids:
        if node_id not in source_node_ids_w_score:
            source_node_ids_w_score[node_id] = 0.0

    extracted_data_source_ids = session.data_source_ids
    source_nodes: list[NodeWithScore] = []
    if len(source_node_ids_w_score) > 0:
        try:
            for ds_id in extracted_data_source_ids:
                node_ids = list(source_node_ids_w_score.keys())
                qdrant_store = VectorStoreFactory.for_chunks(ds_id)
                vector_store = qdrant_store.llama_vector_store()
                extracted_source_nodes = vector_store.get_nodes(node_ids=node_ids)

                # cast them into NodeWithScore with score 0.0
                source_nodes.extend(
                    [
                        NodeWithScore(
                            node=node,
                            score=source_node_ids_w_score.get(node.node_id, 0.0),
                        )
                        for node in extracted_source_nodes
                    ]
                )
        except Exception as e:
            logger.warning(
                "Failed to extract nodes from response citations (%s): %s",
                extracted_node_ids,
                e,
            )
            pass
    return source_nodes


def build_datasource_query_components(
    data_source_id: int,
) -> tuple[BaseEmbedding, VectorStoreIndex]:
    qdrant_store = VectorStoreFactory.for_chunks(data_source_id)
    vector_store = qdrant_store.llama_vector_store()
    embedding_model = qdrant_store.get_embedding_model()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )
    return embedding_model, index


def query(
    session: Session,
    query_str: str,
    configuration: QueryConfiguration,
    chat_history: list[RagContext],
) -> tuple[AgentChatResponse, str | None]:
    llm = models.LLM.get(model_name=configuration.model_name)
    retriever = build_retriever(configuration, session.data_source_ids, llm)

    chat_engine = build_flexible_chat_engine(configuration, llm, retriever)

    if not chat_engine:
        raise HTTPException(
            status_code=500,
            detail="Chat engine is not initialized. Please check the configuration.",
        )

    chat_messages = list(
        map(
            lambda message: ChatMessage(role=message.role, content=message.content),
            chat_history,
        )
    )

    condensed_question: str = chat_engine.condense_question(
        chat_messages, query_str
    ).strip()

    try:
        chat_response: AgentChatResponse = chat_engine.chat(query_str, chat_messages)
        logger.debug("query response received from chat engine")
        return chat_response, condensed_question
    except botocore.exceptions.ClientError as error:
        logger.warning(error.response)
        json_error = error.response
        raise HTTPException(
            status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
            detail=json_error["StatusReason"],
        ) from error


def build_retriever(
    configuration: QueryConfiguration,
    data_source_ids: list[int],
    llm: LLM,
) -> Optional[BaseRetriever]:
    retrievers: list[FlexibleRetriever] = []
    for data_source_id in data_source_ids:
        if data_source_id is None:
            continue

        embedding_model, vector_store = build_datasource_query_components(
            data_source_id
        )
        retriever = FlexibleRetriever(
            configuration, vector_store, embedding_model, data_source_id, llm
        )
        retrievers.append(retriever)
    return MultiSourceRetriever(retrievers)
