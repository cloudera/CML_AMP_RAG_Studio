# MCP.json Configuration Guide

This document provides guidance on how to update and maintain the `mcp.json` file, which defines external tools and services that can be used by the RAG Studio application.

## Purpose

The `mcp.json` file defines "MCP servers" which are external tools or services that can be integrated with the application. These tools can be used during query processing to enhance the capabilities of the system.

## File Structure

The `mcp.json` file has the following structure:

```json
{
  "mcp_servers": [
    {
      "name": "server-name",
      "command": "command-to-execute",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR_NAME": "env_var_value"
      },
      "metadata": {
        "display_name": "Human-readable name",
        "description": "Description of the tool"
      }
    },
    {
      "name": "url-based-server",
      "url": ["http://server-url/endpoint"],
      "metadata": {
        "display_name": "Human-readable name",
        "description": "Description of the tool"
      }
    }
  ]
}
```

## Server Types

There are two types of server configurations supported:

1. **Command-based servers**: These servers are executed as local commands.
   - Required fields: `name`, `command`, `metadata`
   - Optional fields: `args` (array of command arguments), `env` (object with environment variables)

2. **URL-based servers**: These servers are accessed via HTTP.
   - Required fields: `name`, `url`, `metadata`
   - The `url` field should contain an array with at least one URL.

## Environment Variables Support

Command-based servers can use environment variables through the `env` field. This allows you to:

- Configure tool behavior through environment variables
- Override system environment variables specifically for this tool

The `env` field is an object where:
- Keys are environment variable names
- Values are the corresponding environment variable values

These environment variables are only set for the specific tool process and do not affect the global environment or other tools.

## How to Add a New Tool

To add a new tool to the `mcp.json` file:

1. Determine whether your tool is command-based or URL-based.
2. Add a new entry to the `mcp_servers` array with the appropriate fields.
3. Ensure that the `name` field is unique across all servers.
4. Include descriptive `metadata` to help users understand the purpose of the tool.

### Example: Adding a Command-based Tool

```json
{
  "name": "my-new-tool",
  "command": "tool-executable",
  "args": ["--option", "value"],
  "env": {
    "API_KEY": "your-api-key",
    "DEBUG_MODE": "true"
  },
  "metadata": {
    "display_name": "My New Tool",
    "description": "This tool performs a specific function"
  }
}
```

### Example: Adding a URL-based Tool

```json
{
  "name": "my-api-tool",
  "url": ["http://api.example.com/endpoint"],
  "metadata": {
    "display_name": "My API Tool",
    "description": "This tool connects to an external API"
  }
}
```

## How to Modify Existing Entries

To modify an existing tool:

1. Locate the entry in the `mcp_servers` array by its `name`.
2. Update the fields as needed, ensuring that the required fields for the server type are maintained.
3. If changing the server type (e.g., from command-based to URL-based), ensure that all required fields for the new type are included.

## Validation Requirements

When updating the `mcp.json` file, ensure that:

1. The file contains valid JSON syntax.
2. The `mcp_servers` field is an array.
3. Each server entry has a unique `name`.
4. Each server entry includes either a `command` field (for command-based servers) or a `url` field (for URL-based servers).
5. Each server entry includes a `metadata` object with `display_name` and `description` fields.

## Usage in the Application

The tools defined in `mcp.json` are:
- Listed in the UI for users to select when configuring queries
- Used to create adapters that can be utilized during query processing
- Accessible through the `/tools` API endpoint

After updating the `mcp.json` file, restart the application for the changes to take effect.
