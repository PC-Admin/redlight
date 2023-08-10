
# Hashing room_ids


## Possible Options

    SHA-2 Family: SHA-512, which you mentioned, belongs to this family. Other members include SHA-256, SHA-384, and more. They are widely used and are currently considered secure.

    SHA-3: This is the successor to SHA-2 and was standardized by NIST (U.S. National Institute of Standards and Technology) in 2015. SHA-3 is not a modification of SHA-2 but is derived from a cryptographic primitive called Keccak.

    BLAKE2: An alternative to MD5 and SHA-2/3, it's considered high-speed and secure. There's also a successor, BLAKE3, which is even faster and maintains a high-security level.

    Whirlpool: This is a cryptographic hash function that produces a 512-bit hash. It has undergone a few revisions and is currently considered secure.

    RIPEMD-160: While it produces a shorter hash (160 bits), it's still considered reasonably secure and is used in certain applications like Bitcoin.

    Argon2: Though not a general-purpose hash function like the others, Argon2 is notable as a memory-hard password hashing function. It's designed to be resistant against GPU-based attacks and is the winner of the Password Hashing Competition in 2015.


## Testing
```
$ time (echo -n '!OEedGOAXDBahPyWMSQ:example.com' | sha512sum | cut -d ' ' -f1 | xargs echo -n | sha512sum)
d5e0b4e8ee49f16b353be2320aa998f2973506e0dccfe9d377d460253e9a6b98966d9d959dfa1501a33a7781eb4cc18eab1cbf03ba3c0fbe98979aa5f163abc7  -

real	0m0.003s
user	0m0.004s
sys	0m0.002s

$ time echo -n '!zWTEwEwdqIvmcJpytH:perthchat.org' | sha256sum -b | cut -d ' ' -f1 | xxd -r -p | sha256sum
962c56a12d861d1921073916db9a1fb47ccc7887d3199690f1de156e57cac709  -

real	0m0.002s
user	0m0.005s
sys	0m0.001s

$ sudo apt install rhash
$ time echo -n '!OEedGOAXDBahPyWMSQ:example.com' | rhash --sha3-512 - 
1eb131ffdd0384fee5465cb3ef10ac95d9cd20e1de0e1b56475c44df095c20b61602de183f0fc0cec49d7e291d06b5169f0134e45923ab5814c42f57353dbb8b  (stdin)

real	0m0.002s
user	0m0.003s
sys	0m0.000s

$ time echo -n '!OEedGOAXDBahPyWMSQ:example.com' | b2sum | cut -d ' ' -f1 | xargs echo -n | b2sum
070034bf542d1cb43026b9f51aabbb28243a67cc0a26a23aa2221ff3f185f0a643bb693d39a3525b68d142b4698f3ba755e0eb90c992580376d867aa1ed5d23e  -

real	0m0.003s
user	0m0.007s
sys	0m0.000s
```


## Final Choice

As sha256sum has shorter output and it supported by Python's built in libraries it seems ideal?
