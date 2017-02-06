#!/usr/bin/python
from Crypto.Util.number import *

def genkey(k, e = 65537):
    while True:
        p = getPrime(k/2)
        q = getPrime(k/2)
        n = p*q
        if GCD((p-1)*(q-1), e) == 1:
            break
    return n

print genkey(128)

