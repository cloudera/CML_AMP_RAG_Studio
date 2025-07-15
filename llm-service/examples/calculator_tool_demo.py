#!/usr/bin/env python3
"""
Standalone Calculator Tool Demo

This script demonstrates the calculator tool definition and testing
without requiring the RAG Studio API to be running.
"""

import json

# This is the exact tool definition format used in the user tools system
CALCULATOR_TOOL_DEFINITION = {
    "name": "simple_calculator",
    "display_name": "Simple Calculator",
    "description": "Performs basic arithmetic operations on two numbers",
    "function_schema": {
        "type": "object",
        "properties": {
            "first_number": {
                "type": "number",
                "description": "The first number in the operation",
            },
            "second_number": {
                "type": "number",
                "description": "The second number in the operation",
            },
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "The arithmetic operation to perform",
            },
        },
        "required": ["first_number", "second_number", "operation"],
    },
    "function_code": '''def simple_calculator(first_number: float, second_number: float, operation: str) -> float:
    """
    Performs basic arithmetic operations on two numbers.
    
    Args:
        first_number: The first number in the operation
        second_number: The second number in the operation  
        operation: The arithmetic operation to perform (add, subtract, multiply, divide)
        
    Returns:
        The result of the arithmetic operation
        
    Raises:
        ValueError: If operation is not supported or division by zero
    """
    if operation == "add":
        return first_number + second_number
    elif operation == "subtract":
        return first_number - second_number
    elif operation == "multiply":
        return first_number * second_number
    elif operation == "divide":
        if second_number == 0:
            raise ValueError("Cannot divide by zero")
        return first_number / second_number
    else:
        raise ValueError(f"Unsupported operation: {operation}")''',
}


def execute_function_code(function_code: str, function_name: str, **kwargs):
    """
    Execute user function code safely (simulates the dynamic_mcp execution).

    This is similar to how the actual UserToolDefinition.execute() method works.
    """
    # Create a restricted globals environment (similar to dynamic_mcp.py)
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
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "round": round,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "isinstance": isinstance,
            "type": type,
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

    # Execute the function code in restricted environment
    local_vars = {}
    exec(function_code, safe_globals, local_vars)

    # Get the function and call it
    if function_name in local_vars:
        func = local_vars[function_name]
        return func(**kwargs)
    else:
        raise ValueError(f"Function {function_name} not found in code")


def demo_calculator():
    """Demonstrate the calculator tool definition and usage."""

    print("🔧 Calculator Tool Demo")
    print("=" * 50)

    # Show the tool definition
    print("\n📋 Tool Definition:")
    print(f"Name: {CALCULATOR_TOOL_DEFINITION['name']}")
    print(f"Display Name: {CALCULATOR_TOOL_DEFINITION['display_name']}")
    print(f"Description: {CALCULATOR_TOOL_DEFINITION['description']}")

    print("\n📄 Function Schema:")
    schema = CALCULATOR_TOOL_DEFINITION["function_schema"]
    print(json.dumps(schema, indent=2))

    print("\n🐍 Function Code:")
    print(CALCULATOR_TOOL_DEFINITION["function_code"])

    print("\n" + "=" * 50)
    print("🧪 Testing Calculator Tool")
    print("=" * 50)

    # Test cases
    test_cases = [
        {"first_number": 10, "second_number": 5, "operation": "add", "expected": 15},
        {
            "first_number": 10,
            "second_number": 3,
            "operation": "subtract",
            "expected": 7,
        },
        {
            "first_number": 7,
            "second_number": 6,
            "operation": "multiply",
            "expected": 42,
        },
        {"first_number": 15, "second_number": 3, "operation": "divide", "expected": 5},
        {
            "first_number": 10,
            "second_number": 0,
            "operation": "divide",
            "expected": "ERROR",
        },
    ]

    function_code = CALCULATOR_TOOL_DEFINITION["function_code"]
    function_name = CALCULATOR_TOOL_DEFINITION["name"]

    for i, test_case in enumerate(test_cases, 1):
        expected = test_case.pop("expected")

        print(
            f"\nTest {i}: {test_case['first_number']} {test_case['operation']} {test_case['second_number']}"
        )

        try:
            result = execute_function_code(function_code, function_name, **test_case)
            print(f"  Result: {result}")

            if expected == "ERROR":
                print(f"  ❌ Expected error but got result: {result}")
            elif result == expected:
                print(f"  ✅ Correct! Expected {expected}")
            else:
                print(f"  ❌ Wrong! Expected {expected}, got {result}")

        except Exception as e:
            print(f"  Error: {e}")
            if expected == "ERROR":
                print(f"  ✅ Correct! Expected an error")
            else:
                print(f"  ❌ Unexpected error! Expected {expected}")


def show_api_usage():
    """Show how this tool would be used with the actual API."""

    print("\n" + "=" * 50)
    print("🌐 API Usage Example")
    print("=" * 50)

    print("\n1. Submit the tool:")
    print("```bash")
    print("curl -X POST http://localhost:8000/user-tools \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -H 'origin_remote_user: your_username' \\")
    print("  -d '{")
    print('    "name": "simple_calculator",')
    print('    "display_name": "Simple Calculator",')
    print('    "description": "Performs basic arithmetic operations on two numbers",')
    print('    "function_schema": { ... },')
    print('    "function_code": "def simple_calculator(...): ..."')
    print("  }'")
    print("```")

    print("\n2. Test the tool:")
    print("```bash")
    print("curl -X POST http://localhost:8000/user-tools/simple_calculator/test \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -H 'origin_remote_user: your_username' \\")
    print("  -d '{")
    print('    "input_data": {')
    print('      "first_number": 10,')
    print('      "second_number": 5,')
    print('      "operation": "add"')
    print("    }")
    print("  }'")
    print("```")

    print("\n3. Use in chat:")
    print(
        "Once submitted, the tool is automatically available in RAG Studio chat sessions."
    )
    print("The LLM can call it when users ask mathematical questions:")
    print('  User: "What is 15 divided by 3?"')
    print('  Assistant: *calls simple_calculator(15, 3, "divide")* → "The result is 5"')


def show_more_examples():
    """Show examples of other tools that could be created."""

    print("\n" + "=" * 50)
    print("💡 More Tool Ideas")
    print("=" * 50)

    examples = [
        {
            "name": "text_counter",
            "description": "Count words, characters, and lines in text",
            "example_inputs": {"text": "Hello world!", "count_type": "words"},
            "example_output": 2,
        },
        {
            "name": "temperature_converter",
            "description": "Convert between Celsius, Fahrenheit, and Kelvin",
            "example_inputs": {
                "temperature": 100,
                "from_unit": "celsius",
                "to_unit": "fahrenheit",
            },
            "example_output": 212.0,
        },
        {
            "name": "percentage_calculator",
            "description": "Calculate percentages, percentage change, etc.",
            "example_inputs": {
                "value": 80,
                "total": 200,
                "calculation": "percentage_of",
            },
            "example_output": 40.0,
        },
        {
            "name": "string_formatter",
            "description": "Format strings (uppercase, lowercase, title case, etc.)",
            "example_inputs": {"text": "hello world", "format_type": "title"},
            "example_output": "Hello World",
        },
    ]

    for example in examples:
        print(f"\n📝 {example['name']}")
        print(f"   Description: {example['description']}")
        print(f"   Example Input: {example['example_inputs']}")
        print(f"   Example Output: {example['example_output']}")


if __name__ == "__main__":
    demo_calculator()
    show_api_usage()
    show_more_examples()

    print("\n" + "=" * 50)
    print("🎉 Demo Complete!")
    print("=" * 50)
    print("\nTo actually use this tool:")
    print("1. Start the RAG Studio backend")
    print("2. Run: python calculator_tool_example.py --username your_username")
    print("3. Or use the API directly with curl/requests")
    print("4. Once submitted, use the tool in RAG Studio chat sessions")
