# # Create a file in your assignments folder called `Simple_Calculator.py`. In it, create a calculator that handles a number of different operations. Each operation will be its own function, therefore you will have one function per operation. Each operation only needs to work with two numbers, x and y.

# When ran, the program should use a combination of the `input()` and `print()` functions to ask the user for information about the calculation they are about to run:

# - x value
# - y value

# ---

# ### Requirements
# - Create functions for each of the following operations:
#   - Addition
#   - Subtraction
#   - Multiplication
#   - Division
# - Each function should take two parameters (x and y) and return the result of the operation.
# - The program should handle division by zero gracefully.
# - The program should allow the user to perform multiple calculations without restarting.

def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y == 0:
        return "Error: Division by zero is not allowed."
    return x / y

def exponent(x, y):
    return x ** y

def modulus(x, y):
    if y == 0:
        return "Error: Division by zero is not allowed."
    return x % y

def floor_divide(x, y):
    if y == 0:
        return "Error: Division by zero is not allowed."
    return x // y

def calculator():
    while True:
        print("Select operation:")
        print("1. Addition")
        print("2. Subtraction")
        print("3. Multiplication")
        print("4. Division")
        print("5. Exponentiation")
        print("6. Modulus")
        print("7. Floor Division")
        print("8. Exit")

        choice = input("Enter choice (1-8): ")

        if choice == '8':
            print("Exiting the calculator. Goodbye!")
            break

        if choice in ['1', '2', '3', '4', '5', '6', '7']:
            try:
                x = float(input("Enter first number (x): "))
                y = float(input("Enter second number (y): "))
            except ValueError:
                print("Invalid input. Please enter numeric values.")
                continue

            if choice == '1':
                print(f"{x} + {y} = {add(x, y)}")
            elif choice == '2':
                print(f"{x} - {y} = {subtract(x, y)}")
            elif choice == '3':
                print(f"{x} * {y} = {multiply(x, y)}")
            elif choice == '4':
                print(f"{x} / {y} = {divide(x, y)}")
            elif choice == '5':
                print(f"{x} ** {y} = {exponent(x, y)}")
            elif choice == '6':
                print(f"{x} % {y} = {modulus(x, y)}")
            elif choice == '7':
                print(f"{x} // {y} = {floor_divide(x, y)}")
        else:
            print("Invalid choice. Please select a valid operation.")