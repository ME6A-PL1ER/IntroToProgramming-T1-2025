# Questions prompted to user
animal = input("What is your favorite animal?\n: ")
habitat = input("Where does it live?\n: ")
diet = input("What does it eat?\n: ")
size = input("How big is it?\n: ")
color = input("What color is it?\n: ")
type = input("Is it a pet or wild animal?\n: ")
legs = input("How many legs does it have?\n: ")
covering = input("Does it have fur, feathers, or scales?\n: ")
classification = input("Is it a mammal, bird, reptile, amphibian, or fish?\n: ")
sound = input("What sound does it make?\n: ")

# Stitch all questions into one string and print
summary = f"Your favorite animal is a {animal}. It lives in {habitat}, and it eats {diet}. It is {size} and is {color} in color. It is a {type} animal with {legs} legs. It has {covering} and is classified as a {classification}. The sound it makes is: {sound}."
print(summary)