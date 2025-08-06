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
import re
from typing import Any, Optional, cast, Annotated
from urllib.parse import unquote

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from .... import exceptions
from ....config import settings
from ....services.models import get_model_source, ModelSource
from ....services.models.providers import BedrockModelProvider
from ....services.query.agents.agent_tools.image_generation import (
    BEDROCK_STABLE_DIFFUSION_MODEL_ID,
    BEDROCK_TITAN_IMAGE_MODEL_ID,
    ImageGenerationTools,
    IMAGE_GENERATION_TOOL_METADATA,
)
from ....services.utils import has_admin_rights

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


class ImageGenerationConfig(BaseModel):
    """
    Represents the complete image generation configuration.
    """

    enabled: bool = True
    selected_tool: Optional[str] = None


mcp_json_path: str = os.path.join(settings.tools_dir, "mcp.json")
image_generation_config_path: str = os.path.join(
    settings.tools_dir, "image_generation_config.json"
)


def get_mcp_config() -> dict[str, Any]:
    """
    Reads the MCP configuration from the mcp.json file.
    """
    if not os.path.exists(mcp_json_path):
        raise HTTPException(
            status_code=404,
            detail=f"MCP configuration file not found at {mcp_json_path}",
        )

    try:
        with open(mcp_json_path, "r") as f:
            return cast(dict[str, Any], json.load(f))
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse MCP configuration file at {mcp_json_path}",
        )


def get_image_generation_config() -> ImageGenerationConfig:
    """
    Gets the complete image generation configuration (enabled state + selected tool).
    """
    if not os.path.exists(image_generation_config_path):
        # Default configuration - disabled by default
        return ImageGenerationConfig(enabled=False, selected_tool=None)

    try:
        with open(image_generation_config_path, "r") as f:
            data = json.load(f)
            return ImageGenerationConfig(**data)
    except Exception:
        logger.error(
            "Failed to get image generation config from %s",
            image_generation_config_path,
        )
        # Default configuration - disabled by default
        return ImageGenerationConfig(enabled=False, selected_tool=None)


def set_image_generation_config(config: ImageGenerationConfig) -> None:
    """
    Sets the complete image generation configuration.
    """
    os.makedirs(os.path.dirname(image_generation_config_path), exist_ok=True)
    with open(image_generation_config_path, "w") as f:
        json.dump(config.model_dump(), f, indent=2)


def get_selected_image_generation_tool() -> Optional[str]:
    """
    Gets the currently selected image generation tool.
    Returns None if image generation is disabled or no tool is selected.
    """
    config = get_image_generation_config()

    if not config.enabled:
        return None

    return config.selected_tool


@router.get(
    "",
    summary="Returns a list of available tools.",
    response_model=None,
)
@exceptions.propagates
def tools() -> list[ToolMetadata]:
    # Get MCP tools from config
    mcp_config = get_mcp_config()
    tool_list = [ToolMetadata(**server) for server in mcp_config["mcp_servers"]]

    return tool_list


def get_image_generation_tool_metadata() -> list[ToolMetadata]:
    # Get current model provider
    model_source = get_model_source()
    # Add image generation tools based on the current model provider
    if model_source == ModelSource.OPENAI:
        tool_metadata = IMAGE_GENERATION_TOOL_METADATA[
            ImageGenerationTools.OPENAI_IMAGE_GENERATION
        ]
        return [
            ToolMetadata(
                name=ImageGenerationTools.OPENAI_IMAGE_GENERATION,
                metadata={
                    "description": tool_metadata["description"],
                    "display_name": tool_metadata["display_name"],
                },
            )
        ]
    if model_source == ModelSource.BEDROCK:
        supported_model_ids = [
            BEDROCK_STABLE_DIFFUSION_MODEL_ID,
            BEDROCK_TITAN_IMAGE_MODEL_ID,
        ]
        available_models = BedrockModelProvider.list_image_generation_models()
        supported_bedrock_image_generation_tools = []
        if not available_models:
            return []
        for model in available_models:
            if model.model_id not in supported_model_ids:
                continue
            if model.model_id == BEDROCK_STABLE_DIFFUSION_MODEL_ID:
                tool_metadata = IMAGE_GENERATION_TOOL_METADATA[
                    ImageGenerationTools.BEDROCK_STABLE_DIFFUSION
                ]
                supported_bedrock_image_generation_tools.append(
                    ToolMetadata(
                        name=ImageGenerationTools.BEDROCK_STABLE_DIFFUSION,
                        metadata={
                            "description": tool_metadata["description"],
                            "display_name": tool_metadata["display_name"],
                        },
                    )
                )
            elif model.model_id == BEDROCK_TITAN_IMAGE_MODEL_ID:
                tool_metadata = IMAGE_GENERATION_TOOL_METADATA[
                    ImageGenerationTools.BEDROCK_TITAN_IMAGE
                ]
                supported_bedrock_image_generation_tools.append(
                    ToolMetadata(
                        name=ImageGenerationTools.BEDROCK_TITAN_IMAGE,
                        metadata={
                            "description": tool_metadata["description"],
                            "display_name": tool_metadata["display_name"],
                        },
                    )
                )
        return supported_bedrock_image_generation_tools
    # Return empty list for other model providers
    return []


@router.get(
    "/image-generation",
    summary="Returns a list of available image generation tools.",
    response_model=list[ToolMetadata],
)
@exceptions.propagates
def image_generation_tools() -> list[ToolMetadata]:
    """
    Returns a list of available image generation tools based on the current model provider.
    """
    return get_image_generation_tool_metadata()


@router.get(
    "/image-generation/config",
    summary="Returns the complete image generation configuration.",
    response_model=ImageGenerationConfig,
)
@exceptions.propagates
def get_image_generation_config_endpoint() -> ImageGenerationConfig:
    """
    Returns the complete image generation configuration.
    """
    return get_image_generation_config()


@router.post(
    "/image-generation/config",
    summary="Sets the complete image generation configuration.",
    response_model=ImageGenerationConfig,
)
@exceptions.propagates
def set_image_generation_config_endpoint(
    config: ImageGenerationConfig,
    remote_user: Annotated[str | None, Header()] = None,
    remote_user_perm: Annotated[str, Header()] = None,
) -> ImageGenerationConfig:
    """
    Sets the complete image generation configuration.
    """
    if not has_admin_rights(remote_user, remote_user_perm):
        raise HTTPException(
            status_code=401,
            detail="You do not have permission to modify tool settings.",
        )

    # If enabling and selecting a tool, validate that the tool exists
    if config.enabled and config.selected_tool is not None:
        available_tools = get_image_generation_tool_metadata()
        available_tool_names = [tool.name for tool in available_tools]

        if config.selected_tool not in available_tool_names:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tool selection. Available tools: {available_tool_names}",
            )

    set_image_generation_config(config)
    return config


@router.post(
    "",
    summary="Adds a new tool to the MCP configuration.",
    response_model=Tool,
)
@exceptions.propagates
def add_tool(
    tool: Tool,
    remote_user: Annotated[str | None, Header()] = None,
    remote_user_perm: Annotated[str, Header()] = None,
) -> Tool:
    if not has_admin_rights(remote_user, remote_user_perm):
        raise HTTPException(
            status_code=401, detail="You do not have permission to add tools."
        )

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
def delete_tool(
    name: str,
    remote_user: Annotated[str | None, Header()] = None,
    remote_user_perm: Annotated[str, Header()] = None,
) -> None:
    if not has_admin_rights(remote_user, remote_user_perm):
        raise HTTPException(
            status_code=401, detail="You do not have permission to delete tools."
        )

    decoded_name = unquote(name)

    # Prevent deletion of image generation tools
    available_image_tools = get_image_generation_tool_metadata()
    image_tool_names = [tool.name for tool in available_image_tools]

    if decoded_name in image_tool_names:
        raise HTTPException(
            status_code=400,
            detail="Image generation tools cannot be deleted.",
        )

    mcp_config = get_mcp_config()

    # Find the tool with the given name
    tool_found = False
    updated_servers = []
    for server in mcp_config["mcp_servers"]:
        if server["name"] == decoded_name:
            tool_found = True
        else:
            updated_servers.append(server)
    mcp_config["mcp_servers"] = updated_servers

    if not tool_found:
        raise ValueError(f"Tool with name '{decoded_name}' not found")

    # Write the updated config back to the file
    with open(mcp_json_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    return None
