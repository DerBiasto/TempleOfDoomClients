n = int(input())
x = 0
y = 1

for i in range(n):
    k = x + y
    y = x
    x = k
print(k)    #printed die  n-te fibonaccizahl


