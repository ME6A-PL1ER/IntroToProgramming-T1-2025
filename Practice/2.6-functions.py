def add_five_numbers(a, b, c, d, e):
    if not all(isinstance(i, (int, float)) for i in [a, b, c, d, e]):
        raise ValueError("All arguments must be numbers.")
    if None in [a, b, c, d, e]:
        raise ValueError("All five arguments must be provided.")
    return a + b + c + d + e

def full_name(first_name, last_name):
    if not first_name or not last_name:
        raise ValueError("Both first name and last name must be provided.")
    return f"{str(first_name)} {str(last_name)}"

def area_calc(l, w, h):
    if not isinstance(l, (int, float)) or not isinstance(w, (int, float)) or not isinstance(h, (int, float)):
        raise ValueError("All arguments must be numbers")
    if None in [l, w, h]:
        raise ValueError("All arguments must be provided")
    return l * w * h

# im tired of checking for types
def word_smash(a, b):
    return f"{str(a)} {str(b)}"

def echo(word, n):
    return str(word) * abs(n)

def happy_birthday(name):
    return f"happy birthday to you,\nhappy birthday to you,\nhappy birthday dear {str(name)},\nhappy birthday to you"

