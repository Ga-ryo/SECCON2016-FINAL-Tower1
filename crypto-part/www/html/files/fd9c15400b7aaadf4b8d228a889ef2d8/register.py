# -*- coding: utf-8 -*-
from Crypto.Util.number import *
import time, hashlib, hmac
import requests
import json

URL = "http://hall.1.finals.seccon.jp/"

def calc_proof_of_work(ts):
    i = 0
    while True:
        d = hashlib.sha1(str(ts) + "|" + str(i)).hexdigest()
        if d[:6] == "000000":
            break
        i += 1
    print "Proof-of-work found"
    return str(i)


def genkey(k, e = 65537):
    p = getPrime(k/2)
    q = getPrime(k/2)
    n = p*q
    d = inverse(e, (p-1)*(q-1))
    return (n, e, d)

def sign(m, n, d):
    return pow(m, d, n)

def register(name, token):
    (n, e, d) = genkey(128)
    ts = int(token[:8], 16)
    msg = (bytes_to_long(name) << 32) + ts
    sig = sign(msg, n, d)
    params = {
        "cmd": "register",
        "n": str(n),
        "e": str(e),
        "sig": str(sig),
        "name": str(name),
        "token": str(token),
        "proof_of_work": calc_proof_of_work(ts)
    }
    r = requests.get(URL, params=params)
    result = json.loads(r.text)
    # print result
    if result["status"] != "ok":
        print result["reason"]
        return

    id = int(result["id"])
    msg = (bytes_to_long("delete") << 32) + id
    unregister_sig = sign(msg, n, d)
    print "%d %d" % (id, unregister_sig)

def unregister(id, sig):
    params = {
        "cmd": "unregister",
        "sig": str(sig),
        "id": str(id),
    }
    r = requests.get(URL, params=params)
    result = json.loads(r.text)
    if result["status"] != "ok":
        print result["reason"]
        return
    print "Done"


if len(sys.argv) == 1:
    print "Usage: r name token"
    print "       u id sig"
    exit(0)
if sys.argv[1] == "r":
    register(sys.argv[2], sys.argv[3])
elif sys.argv[1] == "u":
    unregister(sys.argv[2], sys.argv[3])
