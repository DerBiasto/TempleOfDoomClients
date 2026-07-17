zahl = int(input())
primzahlen = []
while zahl_neu > 1:
    isPrime = True
    zahl_neu = zahl - 1
        if zahl%zahl_neu == 0:  
            while zahl_neu < teiler:
                if zahl%teiler == 0:
                    isPrime = False
                    break
                else:
            
                    teiler = teiler + 1
            
        else:
            zahl_neu = zahl_neu - 1
        if isPrime:
            primzahlen.append[zahl_neu]

