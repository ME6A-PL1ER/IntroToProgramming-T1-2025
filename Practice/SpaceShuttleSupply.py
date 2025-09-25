# Countdown input
from time import sleep


countdown = input("How many seconds until lift-off?\n: ")

# Supply list inputs
oxygen = int(input("How many oxygen tanks are available?\n: "))
food_packs = int(input("How many food packs are available?\n: "))
water_packs = int(input("How many water packs are available?\n: "))

# Line break for readability
print()

# Output the supply list
print("Supply list:")
print(f"Oxygen tanks: {oxygen}")
print(f"Food packs: {food_packs}")
print(f"Water packs: {water_packs}")

# Line break for readability
print()

# Confirm oxygen supply
confirm = input("Is the oxygen supply correct? (yes/no)\n: ")
if confirm.lower() == "yes":
    print("Oxygen supply confirmed.")
else:
    print("Oxygen supply not confirmed, enter new amount.")
    oxygen = int(input("How many oxygen tanks are available?\n: "))
    print(f"Oxygen tanks updated to: {oxygen}")

# Line break for readability
print()

# List all supplies again
print("Supply list:")
print(f"Oxygen tanks: {oxygen}")
print(f"Food packs: {food_packs}")
print(f"Water packs: {water_packs}")

# Line break for readability
print()

# Countdown to lift-off
print("Countdown to lift-off:")
for i in range(int(countdown), 0, -1):
    print(i)
    sleep(1)  # Pause for 1 second between counts
print("Lift-off!")