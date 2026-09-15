---
description: "The LFSR stream, import-name cipher, and sparse per-page code transform."
---

# LFSR, string, and page transforms

## The LFSR keystream

The [per-build bytecode stubs](bytecode-transform.md) are themselves wrapped in an LFSR keystream. The stream is data-independent (seed 1, feedback polynomial `0x8003`, eight bits emitted per byte, LSB first), so it can be replayed at any position. That is what makes trial-decoding candidate stub locations cheap:

```python
def lfsr_keystream(n):
    out = bytearray(n)
    state = 1
    for i in range(n):
        b = 0
        for k in range(8):
            b |= (state & 1) << k
            state = (state << 1) & MASK32
            if state & 0x8000:
                state ^= 0x8003
        out[i] = b
    return out

def lfsr_decrypt_block(d, pos):
    """XOR a bytecode stub with the keystream. The block length is stored
    unencrypted at pos+95."""
    length = d[pos + 95]
    ks = lfsr_keystream(length)
    for i in range(length):
        d[pos + i] ^= ks[i]
```

A stub block occupies a fixed 96-byte slot; the byte at `pos + 95` is the (unencrypted) length of the program inside.

## The import-name string cipher

DLL names and imported function names are encrypted with a rolling byte cipher: nibble swap, subtract the key, step the key by 67. The initial key is the low byte of the string's RVA, so a name can't be decrypted without knowing where it lives.

```python
def string_cipher(d, pos, key):
    """Decrypt a NUL-terminated string in place."""
    i = 0
    while d[pos + i] != 0:
        b = ror8(d[pos + i], 4)
        b = (b - key) & 0xFF
        if b == 0:
            b = (-key) & 0xFF
        d[pos + i] = b
        key = (key + 67) & 0xFF
        i += 1
```

The `b == 0` remap avoids producing a NUL mid-string (which would truncate the walk): if the subtraction yields zero, the byte is replaced by the two's complement of the key instead.

## The per-page code scramble

Executable sections carry a sparse, page-granular scramble on top of everything else: one byte per 16-byte block is XORed, at an in-block offset that varies per block. The pattern skips block 0 (its key state still advances). 255 of each page's 4096 bytes are touched.

```python
def page_scramble(d, va, size, key):
    """64-bit form. `key` is the absolute page index shifted left by a
    build-specific amount (0 or 15)."""
    for i in range(size >> 4):
        mixed = (ror32(key, 15) + i) & MASK32
        key = (mixed + i) & MASK32
        if i == 0:
            continue
        d[va + i * 16 + (mixed & 0xF)] ^= key & 0xFF

def page_scramble_pe32(d, pa, page, big_formula):
    """32-bit form. The page key is (page+1) or 0x8000*(page+1)."""
    key = (0x8000 * (page + 1)) & MASK32 if big_formula else page + 1
    key = ror32(key, 15)
    for bi in range(1, 256):
        rk = ror32(key, 15)
        ri = (rk + bi) & MASK32
        key = (ri + bi) & MASK32
        d[pa + bi * 16 + (ri & 0xF)] ^= key & 0xFF
```

{% hint style="warning" %}
The shift (64-bit: 0 or 15) and the formula choice (32-bit: `page+1` or `0x8000*(page+1)`) are **not recorded anywhere in the file**. Two builds can carry byte-identical configuration stamps yet require different choices. A third outcome is also required: leave the bytes unchanged. Native DLLs often keep plaintext `.text`; applying either formula there still XORs about one byte per 16.

On 64-bit images, a recognized CRT entry stub is stronger evidence than padding counts. The common shape is `48 83 EC ib / E8 rel32 / 48 83 C4 ib / E9 rel32` (the two stack immediates match). Accept a candidate only when it's the sole shift, including “no transform”, whose decoded `call` and `jmp` targets both remain inside `.text`. Unrecognized entry code falls back to padding statistics: replay each shift on sample pages and count positions that become `0xCC`. Require a clear gain over the unchanged bytes (both a margin over the baseline and an absolute floor). Small gains are the noise of XORing 255 pseudo-random positions per page and must not trigger a transform.

On 32-bit images the same `0xCC` comparison chooses between `page+1` and `0x8000*(page+1)`, and skips the pass when neither formula raises the padding count well above the unchanged baseline.
{% endhint %}
