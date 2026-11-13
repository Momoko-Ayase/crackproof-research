---
description: "The 0x8003 LFSR stub cipher, RVA-keyed import-name cipher, and per-page .text code scrambles."
icon: wave-square
---

# LFSR, string, and page transforms

## LFSR keystream (`dd6`)

Each 96-byte [per-build bytecode stub](bytecode-transform.md) slot stores its unencrypted program length at `pos + 95` (`<= 95`) and masks `d[pos .. pos + length]` with a fixed-seed Galois LFSR (initial state `1`, polynomial `0x8003`, 8 bits per byte emitted LSB-first):

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

Because the keystream depends only on byte offset `0..length`, candidate 96-byte windows can be tested at any offset using a precomputed 95-byte keystream table.

## Import-name string cipher (`dd7`)

Encrypted DLL names and imported symbol names use a NUL-terminated rolling byte cipher: swap nibbles (`ror8(..., 4)`), subtract `key`, map `0` to `(-key) & 0xFF` so an interior byte never becomes a premature NUL terminator, and advance `key` by `67`:

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

{% hint style="warning" %}
**Initial `key` for DLL names vs function names.** A DLL name at `name_rva` starts at `pos = name_rva` with `key = name_rva & 0xFF`. A by-name import points to an `IMAGE_IMPORT_BY_NAME` record at `hint_name_rva` whose 2-byte `Hint` precedes the ASCII symbol string: decryption starts at `pos = hint_name_rva + 2`, while the initial key is still `hint_name_rva & 0xFF` (the record RVA, not `(hint_name_rva + 2) & 0xFF`).
{% endhint %}

## Per-page code scramble (`dd8`)

Executable code sections optionally carry an extra sparse XOR pass that flips 1 byte in each of blocks `1..255` (255 bytes per 4,096-byte page; block `0` advances `key` without XORing):

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

{% hint style="info" %}
**Selecting the scramble mode.** Neither the 64-bit shift (`0`, `15`, or unchanged) nor the 32-bit formula (`page + 1`, `0x8000 * (page + 1)`, or unchanged) is stored in the container header, and many native DLLs leave `.text` unscrambled:
1. **64-bit CRT entry check:** test the 18-byte MSVC entry stub (`48 83 EC ib / E8 rel32 / 48 83 C4 ib / E9 rel32` with matching stack immediates) across `unchanged`, `shift 0`, and `shift 15`; select a candidate immediately if it is the unique mode whose `call` and `jmp` targets both land inside `.text`.
2. **64-bit `RET` + `int3` epilogue score:** otherwise sample interior `.text` pages and score total byte length of `0xC3` (`RET`) followed by four or more `0xCC` padding bytes, requiring a gain of at least `8` bytes over the unchanged baseline.
3. **Mutated-byte `0xCC` fallback (64-bit & 32-bit):** only if all `RET + int3` scores are zero on 64-bit (and always on 32-bit), count mutated positions that become `0xCC` and require at least `2x` the unchanged baseline and at least `8` hits; otherwise leave `.text` untouched.
{% endhint %}
