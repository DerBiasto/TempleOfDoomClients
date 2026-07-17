n = int(input())
primzahlen = [2]
i = 1
zahl = 3


while n >= i:
    teiler = 2
    isPrime  = True
    while teiler < zahl:
        if zahl%teiler == 0:
            isPrime = False
            break
        else:
            
            teiler = teiler + 1

    if isPrime:
        primzahlen.append(zahl)
        i = i + 1
    zahl+=1

            

print(primzahlen[n - 1])


        