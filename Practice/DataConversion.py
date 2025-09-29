a = 115         #int -> string
b = 3.14        #float -> string
c = "68"        #string -> int
d = "True"      #string -> boolean
e = True        #boolean -> string
f = False       #boolean -> string
g = '10110111'  #byte -> int
h = "2.54"      #string -> float
i = 100         #int -> float
j = 10.0        #float -> int
k = 254         #int -> byte

a = str(a)
b = str(b)
c = int(c)
d = bool(d)
e = str(e)
f = str(f)
g = int(g)
h = float(h)
i = float(i)
j = int(j)
k = bin(k)

print(a, b, c, d, e, f, g, h, i, j, k)