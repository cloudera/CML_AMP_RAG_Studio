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

import ast
import json
import logging
import os
from typing import Any, Dict, List, Optional, Type, cast

from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, create_model
from app.config import settings

logger = logging.getLogger(__name__)


class UserToolDefinition:
    """
    Represents a user-submitted tool with its schema and code.
    """

    def __init__(
        self,
        name: str,
        display_name: str,
        description: str,
        script_path: str,
    ) -> None:
        self.name = name
        self.display_name = display_name
        self.description = description
        self.script_path = script_path

        # Validate and prepare the function
        self._validate_script_path()
        self._prepare_function()
        self.function_schema = self._extract_function_schema()

    def _extract_function_schema(self) -> Dict[str, Any]:
        """
        Extracts a JSON schema from the main function in the script file.
        """
        with open(self.script_path, "r") as f:
            function_code = f.read()
        tree = ast.parse(function_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_node = node
                break
        else:
            raise ValueError("No function definition found in script.")

        # Extract argument names, types, and docstring
        properties = {}
        required = []
        for arg in func_node.args.args:
            if arg.arg == "self":
                continue
            arg_type = "string"  # default type
            if arg.annotation:
                ann = ast.unparse(arg.annotation)
                if ann in ["int", "float", "bool", "list", "dict"]:
                    arg_type = {
                        "int": "integer",
                        "float": "number",
                        "bool": "boolean",
                        "list": "array",
                        "dict": "object",
                    }[ann]
            properties[arg.arg] = {"type": arg_type}
            required.append(arg.arg)
        docstring = ast.get_docstring(func_node) or ""
        return {
            "title": func_node.name,
            "description": docstring,
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def _validate_script_path(self) -> None:
        """Validate that the script path exists and the code is safe to execute."""
        if not os.path.exists(self.script_path):
            raise ValueError(f"Script file not found: {self.script_path}")

        try:
            with open(self.script_path, "r") as f:
                function_code = f.read()
            # Parse the code to ensure it's valid Python
            tree = ast.parse(function_code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in script: {e}")
        except IOError as e:
            raise ValueError(f"Error reading script file: {e}")

        # Security checks - disallow dangerous imports and operations
        dangerous_patterns = [
            "import os",
            "import subprocess",
            "import sys",
            "import socket",
            "exec(",
            "eval(",
            "__import__",
            "open(",
            "file(",
            "compile(",
            "globals(",
            "locals(",
            "vars(",
        ]

        for pattern in dangerous_patterns:
            if pattern in function_code:
                raise ValueError(f"Dangerous operation detected: {pattern}")

        # Ensure there's at least one function definition
        function_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)

        if not function_names:
            raise ValueError("Script must contain at least one function definition")

    def _prepare_function(self) -> None:
        """Prepare the function for execution."""
        # Read the code from the script file
        with open(self.script_path, "r") as f:
            function_code = f.read()

        # Extract the main function from the code
        tree = ast.parse(function_code)

        # Find the first function definition
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.main_function_name = node.name
                break
        else:
            raise ValueError("No function definition found")

    def _create_input_model(self) -> Type[BaseModel]:
        """Create a Pydantic model from the function schema."""
        properties = self.function_schema.get("properties", {})
        required_fields = self.function_schema.get("required", [])

        # Convert JSON Schema types to Python types
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        field_definitions: Dict[str, Any] = {}
        for field_name, field_schema in properties.items():
            field_type = type_mapping.get(field_schema.get("type", "string"), str)
            default_value = ... if field_name in required_fields else None
            field_definitions[field_name] = (field_type, default_value)

        return cast(
            Type[BaseModel], create_model(f"{self.name}Input", **field_definitions)
        )

    def execute(self, **kwargs: Any) -> Any:
        """Execute the user's function with the provided arguments."""
        try:
            # Create a restricted execution environment
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "max": max,
                    "min": min,
                    "sum": sum,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "reversed": reversed,
                    "print": print,  # Allow print for debugging
                    # Common exceptions
                    "ValueError": ValueError,
                    "TypeError": TypeError,
                    "KeyError": KeyError,
                    "IndexError": IndexError,
                    "ZeroDivisionError": ZeroDivisionError,
                    "AttributeError": AttributeError,
                    "RuntimeError": RuntimeError,
                }
            }

            # Read and execute the function code from script file
            with open(self.script_path, "r") as f:
                function_code = f.read()
            exec(function_code, safe_globals)

            # Get the function from the executed environment
            user_function = safe_globals.get(self.main_function_name)
            if not user_function:
                raise RuntimeError(
                    f"Function '{self.main_function_name}' not found after execution"
                )

            # Ensure it's callable
            if not callable(user_function):
                raise RuntimeError(
                    f"'{self.main_function_name}' is not a callable function"
                )

            # Call the function with the provided arguments
            # We've verified user_function is callable
            result = user_function(**kwargs)

            return result

        except Exception as e:
            logger.error(f"Error executing user tool '{self.name}': {e}")
            raise RuntimeError(f"Tool execution failed: {e}")

    def to_function_tool(self) -> FunctionTool:
        """Convert this user tool to a LlamaIndex FunctionTool."""

        # Create the input model
        input_model = self._create_input_model()

        # Create the function tool
        def tool_function(**kwargs: Any) -> Any:
            try:
                result = self.execute(**kwargs)
                # Ensure result is JSON serializable
                if isinstance(result, (str, int, float, bool, list, dict)):
                    return result
                else:
                    return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        return FunctionTool.from_defaults(
            fn=tool_function,
            name=self.name,
            description=self.description,
            fn_schema=input_model,
        )


class UserToolStorage:
    """
    Unified storage for user tools in mcp.json file.
    """

    def __init__(self) -> None:
        # Use the tools directory from settings
        try:
            self.mcp_json_path = os.path.join(settings.tools_dir, "mcp.json")
            self.scripts_dir = os.path.join(settings.tools_dir, "custom_tool_scripts")
        except ImportError:
            self.mcp_json_path = os.path.join("..", "tools", "mcp.json")
            self.scripts_dir = os.path.join("..", "tools", "custom_tool_scripts")

        # Ensure scripts directory exists
        os.makedirs(self.scripts_dir, exist_ok=True)

    def _read_mcp_config(self) -> Dict[str, Any]:
        """Read the entire mcp.json configuration."""
        if not os.path.exists(self.mcp_json_path):
            return {"mcp_servers": [], "custom_tools": []}

        try:
            with open(self.mcp_json_path, "r") as f:
                config = cast(Dict[str, Any], json.load(f))
                # Ensure custom_tools array exists
                if "custom_tools" not in config:
                    config["custom_tools"] = []
                return config
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading mcp.json: {e}")
            return {"mcp_servers": [], "custom_tools": []}

    def _write_mcp_config(self, config: Dict[str, Any]) -> None:
        """Write the entire mcp.json configuration."""
        try:
            with open(self.mcp_json_path, "w") as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            logger.error(f"Error writing mcp.json: {e}")
            raise RuntimeError(f"Failed to save tool configuration: {e}")

    def save_script_file(self, tool_name: str, file_content: str) -> str:
        """Save a Python script file and return the relative path."""
        script_filename = f"{tool_name}.py"
        script_path = os.path.join(self.scripts_dir, script_filename)

        with open(script_path, "w") as f:
            f.write(file_content)

        # Return relative path for storage in mcp.json
        return os.path.join("custom_tool_scripts", script_filename)

    def save_tool(self, tool: UserToolDefinition) -> None:
        """Save a user tool to mcp.json."""
        config = self._read_mcp_config()

        # Add or update the tool
        tool_data = {
            "name": tool.name,
            "display_name": tool.display_name,
            "description": tool.description,
            "function_schema": tool.function_schema,
            "script_path": tool.script_path,
        }

        # Remove existing tool with same name
        config["custom_tools"] = [
            t for t in config["custom_tools"] if t.get("name") != tool.name
        ]
        config["custom_tools"].append(tool_data)

        # Save to mcp.json
        self._write_mcp_config(config)

    def get_custom_tools(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all custom tools (username parameter ignored for unified storage)."""
        config = self._read_mcp_config()
        return cast(List[Dict[str, Any]], config.get("custom_tools", []))

    def get_tool(self, username: str, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific tool (username parameter ignored for unified storage)."""
        tools = self.get_custom_tools()
        for tool in tools:
            if tool.get("name") == tool_name:
                return tool
        return None

    def delete_tool(self, username: str, tool_name: str) -> bool:
        """Delete a tool (username parameter ignored for unified storage)."""
        config = self._read_mcp_config()

        # Find the tool to get its script path
        tool_to_delete = None
        for tool in config["custom_tools"]:
            if tool.get("name") == tool_name:
                tool_to_delete = tool
                break

        if not tool_to_delete:
            return False  # Tool not found

        # Remove the tool from config
        config["custom_tools"] = [
            t for t in config["custom_tools"] if t.get("name") != tool_name
        ]

        # Delete the script file if it exists
        if "script_path" in tool_to_delete:
            try:
                script_full_path = os.path.join(
                    settings.tools_dir, tool_to_delete["script_path"]
                )
                if os.path.exists(script_full_path):
                    os.remove(script_full_path)
            except (ImportError, OSError) as e:
                logger.warning(f"Could not delete script file: {e}")

        # Save updated config
        self._write_mcp_config(config)
        return True


def create_user_tool_from_dict(tool_data: Dict[str, Any]) -> UserToolDefinition:
    """Create a UserToolDefinition from a dictionary."""
    # Convert relative script path to absolute path
    script_path = tool_data["script_path"]
    if not os.path.isabs(script_path):
        try:
            script_path = os.path.join(settings.tools_dir, script_path)
        except ImportError:
            script_path = os.path.join("..", "tools", script_path)

    return UserToolDefinition(
        name=tool_data["name"],
        display_name=tool_data["display_name"],
        description=tool_data["description"],
        script_path=script_path,
    )


def get_custom_function_tools(username: Optional[str] = None) -> List[FunctionTool]:
    """Get all FunctionTools for custom user-submitted tools.

    Args:
        username: Ignored in unified storage (kept for API compatibility).

    Returns:
        List of FunctionTool objects for all custom tools.
    """
    storage = UserToolStorage()
    tools_data = storage.get_custom_tools()

    function_tools = []
    for tool_data in tools_data:
        try:
            user_tool = create_user_tool_from_dict(tool_data)
            function_tool = user_tool.to_function_tool()
            function_tools.append(function_tool)
        except Exception as e:
            logger.error(
                "Error creating function tool from %s: %s",
                tool_data.get("name", "unknown"),
                e,
            )
            continue

    return function_tools
