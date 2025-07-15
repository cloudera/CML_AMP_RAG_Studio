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
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel

from app import exceptions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/custom-tools", tags=["Custom Tools"])


class UserToolCreateRequest(BaseModel):
    """Request model for creating a user tool."""

    name: str
    display_name: str
    description: str
    function_schema: Dict[str, Any]


class UserToolResponse(BaseModel):
    """Response model for user tools."""

    name: str
    display_name: str
    description: str
    function_schema: Dict[str, Any]
    script_path: str


class UserToolTestRequest(BaseModel):
    """Request model for testing a user tool."""

    input_data: Dict[str, Any]


@router.get("", summary="Get user tools", response_model=List[UserToolResponse])
@exceptions.propagates
def get_user_tools(
    origin_remote_user: Optional[str] = Header(None),
) -> List[UserToolResponse]:
    """Get all tools for the current user."""
    try:
        from app.services.query.agents.agent_tools.dynamic_mcp import UserToolStorage

        username = origin_remote_user or "default_user"
        storage = UserToolStorage()
        tools_data = storage.get_custom_tools()

        return [
            UserToolResponse(
                name=tool["name"],
                display_name=tool["display_name"],
                description=tool["description"],
                function_schema=tool["function_schema"],
                script_path=tool["script_path"],
            )
            for tool in tools_data
        ]
    except Exception as e:
        logger.error(f"Error getting user tools: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tools: {str(e)}")


@router.post("", summary="Create user tool", response_model=UserToolResponse)
@exceptions.propagates
def create_user_tool(
    name: str = Form(...),
    display_name: str = Form(...),
    description: str = Form(...),
    function_schema: str = Form(...),  # JSON string
    script_file: UploadFile = File(...),
    origin_remote_user: Optional[str] = Header(None),
) -> UserToolResponse:
    """Create a new user tool."""
    try:
        import json
        from app.services.query.agents.agent_tools.dynamic_mcp import (
            UserToolDefinition,
            UserToolStorage,
        )

        username = origin_remote_user or "default_user"
        storage = UserToolStorage()

        # Check if tool already exists
        existing_tool = storage.get_tool(username, name)
        if existing_tool:
            raise HTTPException(status_code=400, detail=f"Tool '{name}' already exists")

        # Validate and parse function schema
        try:
            schema_dict = json.loads(function_schema)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid JSON in function_schema: {e}"
            )

        # Validate file type
        if not script_file.filename or not script_file.filename.endswith(".py"):
            raise HTTPException(
                status_code=400, detail="Script file must be a Python (.py) file"
            )

        # Read file content
        file_content = script_file.file.read().decode("utf-8")

        # Save the script file and get the path
        script_path = storage.save_script_file(name, file_content)

        # Create full path for validation
        try:
            from app.config import settings

            full_script_path = os.path.join(settings.tools_dir, script_path)
        except ImportError:
            full_script_path = os.path.join("..", "tools", script_path)

        # Create and validate the tool
        tool = UserToolDefinition(
            name=name,
            display_name=display_name,
            description=description,
            function_schema=schema_dict,
            script_path=full_script_path,
        )

        # Save the tool
        storage.save_tool(tool)

        return UserToolResponse(
            name=tool.name,
            display_name=tool.display_name,
            description=tool.description,
            function_schema=tool.function_schema,
            script_path=script_path,  # Return relative path
        )

    except ValueError as e:
        # Validation errors from tool creation
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user tool: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating tool: {str(e)}")


@router.get("/{tool_name}", summary="Get user tool", response_model=UserToolResponse)
@exceptions.propagates
def get_user_tool(
    tool_name: str, origin_remote_user: Optional[str] = Header(None)
) -> UserToolResponse:
    """Get a specific user tool."""
    try:
        from app.services.query.agents.agent_tools.dynamic_mcp import UserToolStorage

        username = origin_remote_user or "default_user"
        storage = UserToolStorage()

        tool_data = storage.get_tool(username, tool_name)
        if not tool_data:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        return UserToolResponse(
            name=tool_data["name"],
            display_name=tool_data["display_name"],
            description=tool_data["description"],
            function_schema=tool_data["function_schema"],
            script_path=tool_data["script_path"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user tool: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tool: {str(e)}")


@router.put("/{tool_name}", summary="Update user tool", response_model=UserToolResponse)
@exceptions.propagates
def update_user_tool(
    tool_name: str,
    name: str = Form(...),
    display_name: str = Form(...),
    description: str = Form(...),
    function_schema: str = Form(...),  # JSON string
    script_file: UploadFile = File(...),
    origin_remote_user: Optional[str] = Header(None),
) -> UserToolResponse:
    """Update an existing user tool."""
    try:
        import json
        from app.services.query.agents.agent_tools.dynamic_mcp import (
            UserToolDefinition,
            UserToolStorage,
        )

        username = origin_remote_user or "default_user"
        storage = UserToolStorage()

        # Check if tool exists
        existing_tool = storage.get_tool(username, tool_name)
        if not existing_tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        # Validate and parse function schema
        try:
            schema_dict = json.loads(function_schema)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid JSON in function_schema: {e}"
            )

        # Validate file type
        if not script_file.filename or not script_file.filename.endswith(".py"):
            raise HTTPException(
                status_code=400, detail="Script file must be a Python (.py) file"
            )

        # Read file content
        file_content = script_file.file.read().decode("utf-8")

        # Save the script file and get the path (this will overwrite the old file)
        script_path = storage.save_script_file(name, file_content)

        # Create full path for validation
        try:
            from app.config import settings

            full_script_path = os.path.join(settings.tools_dir, script_path)
        except ImportError:
            full_script_path = os.path.join("..", "tools", script_path)

        # Create and validate the updated tool
        tool = UserToolDefinition(
            name=name,
            display_name=display_name,
            description=description,
            function_schema=schema_dict,
            script_path=full_script_path,
        )

        # Save the updated tool
        storage.save_tool(tool)

        return UserToolResponse(
            name=tool.name,
            display_name=tool.display_name,
            description=tool.description,
            function_schema=tool.function_schema,
            script_path=script_path,  # Return relative path
        )

    except ValueError as e:
        # Validation errors from tool creation
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user tool: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating tool: {str(e)}")


@router.delete("/{tool_name}", summary="Delete user tool")
@exceptions.propagates
def delete_user_tool(
    tool_name: str, origin_remote_user: Optional[str] = Header(None)
) -> Dict[str, str]:
    """Delete a user tool."""
    try:
        from app.services.query.agents.agent_tools.dynamic_mcp import UserToolStorage

        username = origin_remote_user or "default_user"
        storage = UserToolStorage()

        success = storage.delete_tool(username, tool_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        return {"message": f"Tool '{tool_name}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user tool: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting tool: {str(e)}")


@router.post("/{tool_name}/test", summary="Test user tool")
@exceptions.propagates
def test_user_tool(
    tool_name: str,
    request: UserToolTestRequest,
    origin_remote_user: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Test a user tool with provided input."""
    try:
        from app.services.query.agents.agent_tools.dynamic_mcp import (
            UserToolStorage,
            create_user_tool_from_dict,
        )

        username = origin_remote_user or "default_user"
        storage = UserToolStorage()

        tool_data = storage.get_tool(username, tool_name)
        if not tool_data:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        # Create the tool and test it
        tool = create_user_tool_from_dict(tool_data)
        result = tool.execute(**request.input_data)

        return {"success": True, "result": result, "input": request.input_data}

    except ValueError as e:
        return {
            "success": False,
            "error": f"Validation error: {str(e)}",
            "input": request.input_data,
        }
    except RuntimeError as e:
        return {
            "success": False,
            "error": f"Execution error: {str(e)}",
            "input": request.input_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing user tool: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "input": request.input_data,
        }
