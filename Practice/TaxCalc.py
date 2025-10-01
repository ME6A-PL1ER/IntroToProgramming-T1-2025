# Rate is in decimal
def calculate_tax(item, price, rate):
    return rate * price

print(calculate_tax("AAH", 10, 0.0625))