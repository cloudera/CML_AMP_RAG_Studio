#!/usr/bin/env python3
"""
Example: Simple Calculator Tool Submission

This script demonstrates how to submit a user tool using the new user tools API.
The calculator tool performs basic arithmetic operations (add, subtract, multiply, divide).
"""

import requests

# Define the calculator tool
CALCULATOR_TOOL = {
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


def submit_calculator_tool(
    api_base_url: str = "http://localhost:8000", username: str = "example_user"
):
    """
    Submit the calculator tool to the user tools API.

    Args:
        api_base_url: Base URL of the RAG Studio API
        username: Username to submit the tool under
    """
    url = f"{api_base_url}/custom-tools"
    headers = {"Content-Type": "application/json", "origin_remote_user": username}

    try:
        response = requests.post(url, json=CALCULATOR_TOOL, headers=headers)
        response.raise_for_status()

        print(f"✅ Successfully submitted calculator tool!")
        print(f"Response: {response.json()}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to submit calculator tool: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response body: {e.response.text}")
        return False


def test_calculator_tool(
    api_base_url: str = "http://localhost:8000", username: str = "example_user"
):
    """
    Test the calculator tool using the test endpoint.

    Args:
        api_base_url: Base URL of the RAG Studio API
        username: Username that owns the tool
    """
    url = f"{api_base_url}/user-tools/simple_calculator/test"
    headers = {"Content-Type": "application/json", "origin_remote_user": username}

    # Test cases
    test_cases = [
        {"first_number": 10, "second_number": 5, "operation": "add"},
        {"first_number": 10, "second_number": 3, "operation": "subtract"},
        {"first_number": 7, "second_number": 6, "operation": "multiply"},
        {"first_number": 15, "second_number": 3, "operation": "divide"},
    ]

    print("\n🧪 Testing calculator tool...")

    for i, test_case in enumerate(test_cases, 1):
        try:
            response = requests.post(
                url, json={"input_data": test_case}, headers=headers
            )
            response.raise_for_status()

            result = response.json()
            expected_results = {"add": 15, "subtract": 7, "multiply": 42, "divide": 5}

            operation = test_case["operation"]
            expected = expected_results.get(operation)
            actual = result.get("result")

            print(
                f"  Test {i}: {test_case['first_number']} {operation} {test_case['second_number']} = {actual}"
            )

            if expected == actual:
                print(f"    ✅ Correct! Expected {expected}")
            else:
                print(f"    ❌ Wrong! Expected {expected}, got {actual}")

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Test {i} failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"    Response: {e.response.text}")


def list_custom_tools(
    api_base_url: str = "http://localhost:8000", username: str = "example_user"
):
    """
    List all custom tools for the given username.
    """
    url = f"{api_base_url}/custom-tools"
    headers = {"origin_remote_user": username}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        tools = response.json()
        print(f"\n📋 Custom tools for {username}:")

        if not tools:
            print("  No tools found")
        else:
            for tool in tools:
                print(f"  - {tool['name']}: {tool['display_name']}")
                print(f"    Description: {tool['description']}")

        return tools

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to list user tools: {e}")
        return []


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculator tool example for RAG Studio user tools"
    )
    parser.add_argument(
        "--api-url", default="http://localhost:8000", help="API base URL"
    )
    parser.add_argument("--username", default="example_user", help="Username to use")
    parser.add_argument(
        "--action",
        choices=["submit", "test", "list", "all"],
        default="all",
        help="Action to perform",
    )

    args = parser.parse_args()

    print(f"🔧 Calculator Tool Example")
    print(f"API URL: {args.api_url}")
    print(f"Username: {args.username}")
    print("-" * 50)

    if args.action in ["submit", "all"]:
        submit_calculator_tool(args.api_url, args.username)

    if args.action in ["test", "all"]:
        test_calculator_tool(args.api_url, args.username)

    if args.action in ["list", "all"]:
        list_custom_tools(args.api_url, args.username)
