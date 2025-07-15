def simple_calculator(first_number: float, second_number: float, operation: str) -> float:
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
        raise ValueError(f"Unsupported operation: {operation}") 