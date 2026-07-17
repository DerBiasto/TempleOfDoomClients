from xmlrpc.client import boolean
x = int(input())
i=1
primes=[2]
a=2

def is_coprime(a, primes):
    for p in primes:
        if a%p==0:
            return False
    return True

while len(primes)<=x:
    if is_coprime(a, primes):
        primes.append(a)
    a += 1

print (primes[x-1])
