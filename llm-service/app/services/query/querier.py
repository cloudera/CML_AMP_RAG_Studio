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
from typing import Optional, TYPE_CHECKING, Tuple

from crewai import CrewOutput
from crewai.tools import BaseTool
from crewai_tools.adapters.mcp_adapter import MCPServerAdapter
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.schema import NodeWithScore, TextNode
from mcp import StdioServerParameters

from .agents.crewai_querier import (
    assemble_crew,
    should_use_retrieval,
    launch_crew,
    stream_chat,
    poison_pill,
)
from .crew_events import CrewEvent
from .flexible_retriever import FlexibleRetriever
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

logger = logging.getLogger(__name__)


def get_mcp_server_adapter(server_name: str) -> MCPServerAdapter:
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
            params = StdioServerParameters(
                command=server_config["command"],
                args=server_config.get("args", []),
                env=environment,
            )
            return MCPServerAdapter(serverparams=params)
        elif "url" in server_config:
            return MCPServerAdapter({"url": server_config["url"][0]})

    raise ValueError(f"Invalid configuration for MCP server '{server_name}'")


def streaming_query(
    chat_engine: Optional[FlexibleContextChatEngine],
    data_source_id: Optional[int],
    query_str: str,
    configuration: QueryConfiguration,
    chat_messages: list[ChatMessage],
    crew_events_queue: Queue[CrewEvent],
    session: Session,
    retriever: Optional[FlexibleRetriever],
) -> StreamingAgentChatResponse:
    mcp_tools: list[BaseTool] = []
    all_adapters: list[MCPServerAdapter] = []

    if session.query_configuration and session.query_configuration.selected_tools:
        for tool_name in session.query_configuration.selected_tools:
            try:
                adapter = get_mcp_server_adapter(tool_name)
                print(
                    f"Adding adapter for tools: {[tool.name for tool in adapter.tools]}"
                )
                all_adapters.append(adapter)
            except ValueError as e:
                logger.warning(f"Could not create adapter for tool {tool_name}: {e}")
                continue

    try:
        for adapter in all_adapters:
            mcp_tools.extend(adapter.tools)

        embedding_model, index = build_datasource_query_components(data_source_id)

        llm = models.LLM.get(model_name=configuration.model_name)

        chat_response: StreamingAgentChatResponse
        if configuration.use_tool_calling:
            use_retrieval, data_source_summaries = should_use_retrieval(
                configuration,
                session.data_source_ids,
                llm,
                query_str,
                chat_messages,
            )

            crew = assemble_crew(
                use_retrieval,
                llm,
                chat_messages,
                query_str,
                crew_events_queue,
                retriever,
                data_source_summaries,
                mcp_tools,
            )
            enhanced_query, crew_result = launch_crew(
                crew,
                query_str,
            )

            source_nodes = get_nodes_from_output(crew_result, session)

            chat_response = stream_chat(
                use_retrieval,
                llm,
                chat_engine,
                enhanced_query,
                source_nodes,
                chat_messages,
            )
            return chat_response
        if not chat_engine:
            raise HTTPException(
                status_code=500,
                detail="Chat engine is not initialized. Please check the configuration.",
            )

        try:
            chat_response = chat_engine.stream_chat(query_str, chat_messages)
            crew_events_queue.put(CrewEvent(type=poison_pill, name="no-op"))
            logger.debug("query response received from chat engine")
        except botocore.exceptions.ClientError as error:
            logger.warning(error.response)
            json_error = error.response
            raise HTTPException(
                status_code=json_error["ResponseMetadata"]["HTTPStatusCode"],
                detail=json_error["StatusReason"],
            ) from error

        return chat_response
    finally:
        for adapter in all_adapters:
            adapter.stop()


def get_nodes_from_output(
    output: str | CrewOutput,
    session: Session,
) -> list[NodeWithScore]:
    source_node_ids_w_score: dict[str, float] = {}
    if isinstance(output, CrewOutput):
        # Extract the retriever results from the crew result
        for task_output in output.tasks_output:
            if task_output.name == "RetrieverTask":
                if task_output.json_dict:
                    json_output = task_output.json_dict["retriever_results"]
                    for result in json_output:
                        node_id = result["node_id"]
                        score = result["score"]
                        if node_id and score:
                            # Append the node id and score to the list
                            source_node_ids_w_score[node_id] = score

    # Extract the node ids from string output
    extracted_node_ids = re.findall(
        r"<a class='rag_citation' href='(.*?)'>",
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
                source_nodes = [
                    NodeWithScore(
                        node=node, score=source_node_ids_w_score.get(node.node_id, 0.0)
                    )
                    for node in extracted_source_nodes
                ]
        except Exception as e:
            logger.warning(
                "Failed to extract nodes from response citations (%s): %s",
                extracted_node_ids,
                e,
            )
            pass
    return source_nodes


def build_datasource_query_components(
    data_source_id: Optional[int],
) -> tuple[Optional[BaseEmbedding], Optional[VectorStoreIndex]]:
    if data_source_id is None:
        return None, None
    qdrant_store = VectorStoreFactory.for_chunks(data_source_id)
    vector_store = qdrant_store.llama_vector_store()
    embedding_model = qdrant_store.get_embedding_model()
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embedding_model,
    )
    return embedding_model, index


def query(
    data_source_id: int,
    query_str: str,
    configuration: QueryConfiguration,
    chat_history: list[RagContext],
) -> tuple[AgentChatResponse, str | None]:
    llm = models.LLM.get(model_name=configuration.model_name)
    retriever = build_retriever(configuration, data_source_id, llm)

    chat_engine = build_flexible_chat_engine(configuration, llm, retriever)

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


def build_retriever(configuration, data_source_id, llm) -> Optional[FlexibleRetriever]:
    embedding_model, vector_store = build_datasource_query_components(data_source_id)
    retriever = (
        FlexibleRetriever(
            configuration, vector_store, embedding_model, data_source_id, llm
        )
        if embedding_model and vector_store
        else None
    )
    return retriever
