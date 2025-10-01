# params and args

def add(x, y):
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError("Both arguments must be numbers.")
    if x is None or y is None:
        raise ValueError("Both arguments must be provided.")
    return x + y

def subtract(x, y):
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError("Both arguments must be numbers.")
    if x is None or y is None:
        raise ValueError("Both arguments must be provided.")
    return x - y

def multiply(x, y):
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError("Both arguments must be numbers.")
    if x is None or y is None: 
        raise ValueError("Both arguments must be provided.")
    return x * y

def divide(x, y):
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError("Both arguments must be numbers.")
    if y == 0:
        raise ValueError("Division by zero is not allowed.")
    if x is None or y is None:
        raise ValueError("Both arguments must be provided.")
    return x / y

def power(x, y):
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError("Both arguments must be numbers.")
    if x is None or y is None:
        raise ValueError("Both arguments must be provided.")
    return x ** y