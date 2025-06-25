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
import logging
import os
from typing import Any, Optional
from urllib.parse import unquote

import re
from fastapi import APIRouter
from pydantic import BaseModel

from .... import exceptions
from ....config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["Tools"])


class ToolMetadata(BaseModel):
    """
    Represents a tool metadata in the MCP configuration.
    """

    name: str
    metadata: dict[str, Any]


class Tool(ToolMetadata):
    """
    Represents a tool in the MCP configuration.
    """

    command: Optional[str] = None
    url: Optional[list[str]] = None
    args: Optional[list[str]] = None
    env: Optional[dict[str, str]] = None


mcp_json_path = os.path.join(settings.tools_dir, "mcp.json")


def get_mcp_config() -> dict:
    """
    Reads the MCP configuration from the mcp.json file.
    """
    if not os.path.exists(mcp_json_path):
        raise FileNotFoundError(f"MCP configuration file not found at {mcp_json_path}")

    with open(mcp_json_path, "r") as f:
        return json.load(f)


@router.get(
    "",
    summary="Returns a list of available tools.",
    response_model=None,
)
@exceptions.propagates
def tools() -> list[ToolMetadata]:

    mcp_config = get_mcp_config()
    return [ToolMetadata(**server) for server in mcp_config["mcp_servers"]]


@router.post(
    "",
    summary="Adds a new tool to the MCP configuration.",
    response_model=Tool,
)
@exceptions.propagates
def add_tool(tool: Tool) -> Tool:

    mcp_config = get_mcp_config()

    # Convert the tool to a dictionary
    tool_dict = tool.model_dump(exclude_none=True)

    # Check if a tool with the same name already exists
    for server in mcp_config["mcp_servers"]:
        pattern = r"^[a-zA-Z0-9-]+$"
        if not bool(re.fullmatch(pattern, tool.name)):
            raise ValueError(
                f"Tool name '{tool.name}' contains invalid characters. "
                "Only alphanumeric characters and hyphens are allowed."
            )
        if server["name"] == tool.name:
            raise ValueError(f"Tool with name '{tool.name}' already exists")

    # Add the new tool to the mcp_servers list
    mcp_config["mcp_servers"].append(tool_dict)

    # Write the updated config back to the file
    with open(mcp_json_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    return tool


@router.delete(
    "/{name}",
    summary="Deletes a tool from the MCP configuration.",
    response_model=None,
)
@exceptions.propagates
def delete_tool(name: str) -> None:
    decoded_name = unquote(name)
    print(f"Deleting tool with name: {decoded_name}")
    mcp_config = get_mcp_config()

    # Find the tool with the given name
    tool_found = False
    mcp_config["mcp_servers"] = [
        server
        for server in mcp_config["mcp_servers"]
        if not (server["name"] == decoded_name and (tool_found := True))
    ]

    if not tool_found:
        raise ValueError(f"Tool with name '{decoded_name}' not found")

    # Write the updated config back to the file
    with open(mcp_json_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    return None
