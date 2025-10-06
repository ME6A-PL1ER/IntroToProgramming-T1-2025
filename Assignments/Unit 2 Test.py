#1:
w1 = input("word 1")
w2 = input("word 2")
w3 = input("word 3")

print(w1 + w2 + w3)

#2:
def add_three(x, y, z):
    print(int(x) + int(y) + int(z))

x = input("int 1")
y = input("int 2")
z = input("int 3")
add_three(x, y, z)

#3:
def data_three():
    word = input("give me a word")
    int = input("give me an int")
    float = input("give me a float")
    floatint = float + int
    concat = str(floatint) + word
    print (concat)

data_three()