import random

def fortune_teller():
    print("Welcome to the Mystic Fortune Teller!")
    
    while True:
        try:
            lucky_number = int(input("Please enter your lucky number (integer): "))
            break
        except ValueError:
            print("That's not a valid integer. Please try again.")
    
    while True:
        try:
            years_ahead = float(input("How many years into the future do you want to see? (float): "))
            break
        except ValueError:
            print("That's not a valid float. Please try again.")
    
    while True:
        try:
            magical_multiplier = float(input("Enter a magical multiplier (float): "))
            break
        except ValueError:
            print("That's not a valid float. Please try again.")
    
    random_factor = random.uniform(1, 10)
    fortune_value = (lucky_number + years_ahead) * magical_multiplier * random_factor
    
    print(f"Your fortune value is: {fortune_value:.2f}")
    if fortune_value > 100:
        print("Great fortune awaits you!")
    elif fortune_value > 50:
        print("Good things are coming your way.")
    else:
        print("Be cautious, challenges may arise.")