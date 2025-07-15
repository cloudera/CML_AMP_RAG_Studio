# User Tools Examples

This directory contains examples demonstrating how to use the RAG Studio User Tools system, which allows users to submit custom Python functions that get wrapped into MCP servers and can be used in chat sessions.

## Overview

The User Tools system enables users to:

- Submit custom Python functions with JSON schema definitions
- Test their tools before using them in chat
- Have their tools automatically validated for security
- Use their tools alongside built-in MCP tools in RAG Studio chat sessions

## Calculator Tool Example

The `calculator_tool_example.py` demonstrates a simple arithmetic calculator tool that can perform basic operations (add, subtract, multiply, divide).

### Running the Example

1. **Start the RAG Studio backend** (make sure it's running on `http://localhost:8000`)

2. **Run the calculator example:**

   ```bash
   cd llm-service/examples
   python calculator_tool_example.py --username your_username
   ```

3. **Or run specific actions:**

   ```bash
   # Just submit the tool
   python calculator_tool_example.py --action submit --username your_username

   # Just test the tool
   python calculator_tool_example.py --action test --username your_username

   # Just list tools
   python calculator_tool_example.py --action list --username your_username
   ```

### What the Example Does

1. **Submits** a calculator tool with:

   - Name: `simple_calculator`
   - Inputs: `first_number`, `second_number`, `operation`
   - Function: Python code that performs arithmetic operations

2. **Tests** the tool with sample calculations:

   - 10 + 5 = 15
   - 10 - 3 = 7
   - 7 × 6 = 42
   - 15 ÷ 3 = 5

3. **Lists** all tools for the user

## Creating Your Own Tools

### Tool Definition Format

Each user tool consists of:

```python
{
    "name": "tool_name",                    # Unique identifier (alphanumeric + underscores)
    "display_name": "Human Readable Name",  # Name shown in UI
    "description": "What this tool does",   # Description for LLM and users
    "function_schema": {                    # JSON Schema for inputs
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "First parameter"
            },
            "param2": {
                "type": "number",
                "description": "Second parameter"
            }
        },
        "required": ["param1", "param2"]
    },
    "function_code": '''def tool_name(param1: str, param2: float) -> str:
        """Your function implementation here"""
        return f"Result: {param1} + {param2}"'''
}
```

### Function Requirements

Your Python function must:

1. **Match the schema**: Function parameters must match the `function_schema` properties
2. **Be self-contained**: No external imports (except safe builtins like `len`, `str`, `int`, etc.)
3. **Be secure**: No file system access, network calls, or dangerous operations
4. **Have type hints**: Input and return types should be specified
5. **Include docstring**: Describe what the function does

### Security Restrictions

For security, user functions cannot:

- Import modules (`import os`, `import subprocess`, etc.)
- Access files (`open()`, `file()`)
- Execute code (`exec()`, `eval()`, `compile()`)
- Access system internals (`globals()`, `locals()`, `__import__`)
- Make network calls (`socket`, `urllib`, etc.)

### Supported Types

Function parameters and return values can be:

- Basic types: `str`, `int`, `float`, `bool`
- Collections: `list`, `dict`
- Optional types: `Optional[str]`, etc.
- Union types: `Union[str, int]`, etc.

## API Endpoints

The user tools system provides these REST endpoints:

- `GET /user-tools` - List all tools for authenticated user
- `POST /user-tools` - Submit a new tool
- `GET /user-tools/{tool_name}` - Get specific tool details
- `PUT /user-tools/{tool_name}` - Update existing tool
- `DELETE /user-tools/{tool_name}` - Delete tool
- `POST /user-tools/{tool_name}/test` - Test tool with sample inputs

## Authentication

All endpoints require the `origin_remote_user` header to identify the user. Each user's tools are isolated from other users.

## Using Tools in Chat

Once submitted and tested, your tools automatically become available in RAG Studio chat sessions. The LLM can call your tools just like any built-in tool when they're relevant to the conversation.

To use a tool in chat:

1. Submit your tool via the API or UI
2. Start a chat session in RAG Studio
3. Ask questions that would benefit from your tool
4. The LLM will automatically call your tool when appropriate

## Example Tools You Could Create

- **Unit Converter**: Convert between different units (meters to feet, celsius to fahrenheit)
- **Text Processor**: Count words, reverse text, format strings
- **Math Helper**: Calculate percentages, compound interest, geometric formulas
- **Data Validator**: Check email formats, phone numbers, credit card numbers
- **Code Generator**: Generate SQL queries, regular expressions, HTML snippets
- **Business Logic**: Calculate taxes, shipping costs, discount pricing

## Troubleshooting

### Common Issues

1. **Tool submission fails**: Check that your function syntax is valid Python
2. **Security validation fails**: Remove any imports or dangerous operations
3. **Schema mismatch**: Ensure function parameters match the JSON schema exactly
4. **Tool not appearing in chat**: Verify the tool was submitted successfully via the list endpoint

### Getting Help

- Check the backend logs for detailed error messages
- Use the test endpoint to debug your function logic
- Ensure your JSON schema validates with online schema validators
