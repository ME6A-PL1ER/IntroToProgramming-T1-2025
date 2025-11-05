fav_fruits = ['grapes', 'strawberries', 'apples', 'bananas', 'mangos']

# Print first
print(fav_fruits[0])
# Print last
print(fav_fruits[-1])
# Add a fruit
fav_fruits.append(input("gimme another fruit"))
# Remove
fav_fruits.remove(input("get rid of one pls"))
# Sort by alphabet
fav_fruits.sort()
print(fav_fruits)

dupe_fruits = ['apples', 'bananas', 'kiwis', 'apples', 'grapes', 'bananas']

# Count occurances
print(dupe_fruits.count('apples'))
# Iterate and print
for fruit in dupe_fruits:
    print(fruit)