# Create a quiz that asks questions and tallies your score at the end.

# ---

# ### Overview

# Use input statements to ask questions and store the answers as variables. Create a function called `tally_score` that checks if the answers are correct. Use if statements to check answers.

# Clarity:
# Input statements outside the function, if statements inside the function. No function parameters needed.

# ---

# ### Requirements

# | **Less Comfortable** | **More Comfortable** |
# | --- | --- |
# | 5 questions | 10 questions |

# ---

# ### Hints

# Be mindful of data types and conversions.

q1 = input("What is 2 + 2? ")
q2 = input("What is the capital of France? ")
q3 = input("What is the largest planet in our solar system? ")
q4 = input("What is the boiling point of water in Celsius? ")
q5 = input("What is the smallest prime number? ")

answers = {
    "q1": "4",
    "q2": "Paris",
    "q3": "Jupiter",
    "q4": "100",
    "q5": "2"
}

def tally_score():
    score = 0
    if q1 == answers["q1"]:
        score += 1
    if q2.lower() == answers["q2"].lower():
        score += 1
    if q3.lower() == answers["q3"].lower():
        score += 1
    if q4 == answers["q4"]:
        score += 1
    if q5 == answers["q5"]:
        score += 1
    print(f"Your total score is: {score}/5")

tally_score()