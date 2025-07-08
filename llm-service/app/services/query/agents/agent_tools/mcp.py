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
import json
import os
from copy import copy

from llama_index.core.tools import FunctionTool
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

from app.config import settings


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
