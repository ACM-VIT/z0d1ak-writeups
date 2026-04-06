# VOIDMARKET

| Field      | Value |
|------------|-------|
| Category   | Cryptography |
| Points     | 100 |
| Solves     | 54 |

## Description

The underground's most secretive trading platform just went dark after a researcher dumped its backend data.
Inside the dump: an encrypted file and a marketplace listing frozen at the moment of seizure. The admin was paranoid. He encrypted his own identity with RSA before storing it anywhere but paranoia doesn't fix bad math. Find the admin's handle. That's one part of your flag and the rest is encoded somewhere in either of the two given files.

Flag Format:
`hackzero{}`

## Files

- [VOIDMARKET.rar](./VOIDMARKET.rar)

## Writeup

#VOIDMARKET 

> `Flag:` `hackzero{sp3ctr4l}`
I liked this one because it is short, but the logic is very nice.

1. Challenge idea I saw
I got 2 files from the archive:

identity.txt
listing.txt
In identity.txt, I saw:

e = 3
big n
big c
note saying: encrypted value is SHA256(admin_handle)
So RSA is used, but with textbook RSA (no padding), and small public exponent (e=3).

2. Main weakness
RSA encryption here is:

c = m^e  modn


Since e = 3, if message m is small enough, then m^3 < n, i.e., which mean modulo never wraps.

So then:

c = m ^ 3
 
That is the full break.

m= 3 root(c)
# 1) extract files
from winrar,
# 2) read files
cat identity.txt
cat listing.txt
Then I solved with Python:

python3 - << 'PY'
from hashlib import sha256

n=int("138120923982166296661006671864764146912021480088786929018040637217769791362267053770816696435130772148965149452523939873617789166584792236706978343345338798143519071942151687774607262234139696833666045471437553192013539148856910997483152951598882616685332703453640775037783535029276614514075507940417165193483")
e=3
c=int("867591158579246807501160551341241871883641905683866432497912775534224554727350147383964938246059863782452724461435181129920391624976456082322755844003513724408128626483829745856326527952523825546559780273582259358037239201375455643")

# integer cube root
lo, hi = 0, 1
while hi**3 <= c:
    hi *= 2
while lo + 1 < hi:
    mid = (lo + hi) // 2
    if mid**3 <= c:
        lo = mid
    else:
        hi = mid

m = lo
print("perfect cube:", m**3 == c)
print("m (hex):", hex(m)[2:])
print("sha256(sp3ctr4l):", sha256(b"sp3ctr4l").hexdigest())
PY
Output gave me:

m (hex) = d2dccfdfd733bbbc813b0638681ef2b96f4cb3d2128bc95125619a36b264f483
and sha256("sp3ctr4l") matched exactly.
So recovered hash = SHA256(sp3ctr4l)
i.e., which mean admin handle is sp3ctr4l.

4. Flag
hackzero{sp3ctr4l}

## Author

ret2.libc
