---
description: "GF(2^32) word mix, stream-header and record ciphers, and the 0x9D protected descriptor."
---

# Word, stream, and record ciphers

Android streams don't reuse the Windows rolling-XOR family. Word mixing is multiplication in GF(2³²). Stream headers, record descriptors, and the `0x9D` protected descriptor each wrap that mix in a different feedback rule. Constants differ across families; treat the values on this page as observed material, not a single universal key.

## GF(2³²) multiply

`gf(w)` multiplies `w` by the fixed element `0x94511dd2` in GF(2³²) with reduction polynomial `0x579357eb`:

```python
MASK32 = 0xFFFFFFFF

def gf32_mul_fixed(value):
    multiplier = 0x94511DD2
    result = 0
    while multiplier:
        if multiplier & 1:
            result ^= value
        carry = value >> 31
        value = (value << 1) & 0xFFFFFFFF
        if carry:
            value ^= 0x579357EB
        multiplier >>= 1
    return result
```

Every later formula on this page, and the [container header](container.md), calls this function.

## Stage 1 word cipher

The 32-byte parameter header and the stage 2 image use unsigned 32-bit wraparound. For word index `i` and family constant `C`:

```
plain[i] = (cipher[i] + (i + 3) * key) XOR (C * (i + 1))
```

Observed `C` values are `0xbf20165d` and `0xbf189bdd`, one per family. The first word is the key and is written back after the 32-byte header is decrypted. Field checks live on [Stage 1 header](../file-format/stage1.md).

## Stream-header cipher

Each interpreter stream starts with two little-endian dwords (`cipher0`, `cipher1`). The stream identifier (`0xE2` at the root, then `0xE3`–`0xE8`) mixes into a per-stream seed that then decrypts every `0x5c`-byte descriptor.

Two constant sets have been observed. They share the `sid * 0x9D323CD7` product and the `gf` mix of the header words; the added constants and the shift assembly differ.

**First observed constant set**

```
K = sid * 0x9D323CD7
K = ((K << (sid & 0xB)) + (K >> (sid & 7))) & 0xFFFFFFFF
dw0 = gf(cipher0 + 0xCBF0C1D8) ^ (K + 0x4178CB33)
dw1 = gf(cipher0 + cipher1)    ^ (K + 0xF119421B)
G   = (K + 0x5590AD79 + dw1) & 0xFFFFFFFF
```

**Second observed constant set**

```
K    = sid * 0x9D323CD7
mix  = (K >> (sid & 7)) + 0x5E727D74
mix  = (mix + (K << (sid & 0xB)) + 0xF71E3005) & 0xFFFFFFFF
dw0  = gf(cipher0 + 0xCBF0C1D8) ^ (0xEBE81DBA + mix)
dw1  = gf(cipher1 + cipher0)    ^ (0xEBE81DBA * 5 + mix)
G    = (dw1 + mix) & 0xFFFFFFFF
```

`G` is the descriptor-cipher seed for that whole stream. Structural checks in [Stage 2 streams](../file-format/stage2-streams.md) stay in force regardless of which constant set a build uses.

## Record-descriptor cipher

Each 0x5c-byte descriptor is 23 little-endian dwords. The walk is the same in both families once `G` is known:

```python
def rec_decrypt(G, idx, rec):
    product = ((G + 0x96F60B71) * G) & MASK32
    record_mask = (product << ((idx + 1) & 3)) & MASK32
    stream_mix = (G * 0x06A55BCC + product) & MASK32
    feedback = 0xF02F7685
    acc = 0x79934CF6
    for off in range(0, 0x5C, 4):
        cipher = get_u32(rec, off)
        square = (feedback * feedback) & MASK32
        value = gf32_mul_fixed(cipher ^ (square >> 3))
        value = (value ^ record_mask) & MASK32
        value = (value + acc + G) & MASK32
        value = (value - (stream_mix >> ((off + 3) & 5))) & MASK32
        put_u32(rec, off, value)
        acc = (acc + 0xE64D33D8) & MASK32
        feedback = cipher
```

`(off + 3) & 5` is a bitwise AND, not a constant 3: word 0 shifts by 1, word 1 by 5, and the pair alternates. Reading it as the constant 3 silently decrypts garbage. `G` is constant for the stream; `idx` changes `record_mask` per descriptor; `feedback` carries the previous *ciphertext* word.

## The `0x9D` protected descriptor

Module `0x9D` begins with another 0x5c-byte record, re-encrypted with the configuration module's header seed `S`:

```python
def decrypt_protected_descriptor(data, seed):
    base0 = ((seed + 0xD3E87144) * seed) & MASK32
    base1 = (base0 + seed * 0x0BD9418D) & MASK32
    words = [0] * (0x5C // 4)
    for i in range(len(words)):
        cipher = get_u32(data, i * 4)
        sub = (base0 << (4 if i & 1 else 0)) & MASK32
        words[i] = ((cipher - sub) ^ (base1 >> ((seed + i * 4) & 7))) & MASK32
    return words
```

Observed plaintext: `command_id == 0x9D`, `outer_offset == 0x5C`, and reserved words after the first six equal zero. Those six words give the outer container offset/size and the auxiliary (relocation) container offset/size used on [Container transforms](container.md).
