---
description: "The rolling XOR, dword rotation, and byte rotation transforms used by Windows payload stages."
---

# Rolling-key and rotation ciphers

Every layer of the container is built from a small set of primitives. Once each one is defined, the staged loader is "apply primitive N at offset X with key Y" repeated in a strict order. This page defines each primitive precisely, with a Python implementation.

{% hint style="success" %}
Every code snippet on this page has been executed and verified against the algorithms as implemented in protected binaries: each function's output was compared byte-for-byte with a reference port on identical inputs.
{% endhint %}

## Conventions

All buffers are mutable byte arrays (`bytearray`); the original algorithms work in place. Helpers used throughout:

```python
MASK32 = 0xFFFFFFFF

def get_u16(d, off):
    return d[off] | (d[off + 1] << 8)

def get_u32(d, off):
    return d[off] | (d[off + 1] << 8) | (d[off + 2] << 16) | (d[off + 3] << 24)

def put_u32(d, off, value):
    d[off:off + 4] = (value & MASK32).to_bytes(4, "little")

def rol32(x, n): return ((x << n) | (x >> (32 - n))) & MASK32
def ror32(x, n): return ((x >> n) | (x << (32 - n))) & MASK32
def rol8(x, n):  return ((x << n) | (x >> (8 - n))) & 0xFF
def ror8(x, n):  return ((x >> n) | (x << (8 - n))) & 0xFF
```

## The rolling-key family

Two ciphers share one rolling-key design: the key starts from a seed, each cell is XORed with the current key, and the key then rolls forward by mixing in the cell value, the loop index, and the square of the index. The header KDF (see [Container and encrypted header](../file-structure/container-layout.md)) is the 8-cell instance; the payload body cipher is the long-form instance with a different seed and update rule:

```python
def payload_xor_chain(file_data, out, info, decrypt_size):
    """Decrypt the bulk of the payload into the image buffer."""
    base_src = (info[4] + 4096) & MASK32
    k = (info[0] + (~decrypt_size & MASK32)) & MASK32
    for i in range(decrypt_size >> 2):
        cell = get_u32(file_data, (base_src + 4 * i) & MASK32)
        put_u32(out, (info[3] + 4 * i) & MASK32, k ^ cell)
        k = (i * i) ^ ((k + cell + i) & MASK32)
```

Because the key rolls forward with each dword, the chain must be decrypted from the start. Random access into the payload is impossible without replaying the chain.

## XOR + rotate-right dword cipher

This cipher unwraps each stage's pointer blocks. It reads a `(base_addr, length)` descriptor from the buffer itself, then transforms each dword: XOR with the rolling key, rotate right by a fixed shift, and subtract the loop index. The shift is 19 or 21 depending on the call site.

```python
def xor_ror_dwords(d, pos, key, shift):
    base_addr = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    for i in range(length >> 2):
        off = (base_addr + 4 * i) & MASK32
        v = get_u32(d, off) ^ key
        key = (key + i) & MASK32
        put_u32(d, off, (ror32(v, shift) - i) & MASK32)
```

32-bit builds additionally brute-force the shift for one stage from the candidate set `[19, 21, 17, 23, 15, 25, 13, 11]`, accepting the shift whose output parses as a valid stage table (see [Loading and section recovery](../loading-and-pe-repair/loading/README.md)).

## Triple byte-rotation ciphers

Two byte ciphers share a structure: three bit-rotations per byte, with two rolling key bytes XORed between rotations. They differ in rotation amount and in how the initial key is derived.

```python
def byte_rotate3(d, pos):
    """Descriptor-addressed variant: rotate by 3, keyed from the address."""
    base_addr = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    b = ((base_addr >> 8) + base_addr) & 0xFF
    b2 = (b + 1) & 0xFF
    for i in range(length):
        idx = base_addr + i
        x = rol8(d[idx], 3) ^ b2
        x = rol8(x, 3) ^ b
        d[idx] = rol8(x, 3)
        b = (b + 1) & 0xFF
        b2 = (b2 + 1) & 0xFF

def byte_rotate2(d, va, size):
    """Position-keyed variant: rotate by 2, keyed from the address itself."""
    b = va & 0xFF
    b2 = (b + 1) & 0xFF
    for i in range(size):
        idx = va + i
        x = rol8(d[idx], 2) ^ b2
        x = rol8(x, 2) ^ b
        d[idx] = rol8(x, 2)
        b = (b + 1) & 0xFF
        b2 = (b2 + 1) & 0xFF
```

The position-keyed variant has a property the loader's table walks rely on heavily: **each output byte depends only on the input byte and the low 8 bits of its address**. There's no cross-byte state. Any four bytes can therefore be trial-decrypted without touching the rest of the buffer:

```python
def trial_byte_rotate2(d, va):
    """Non-mutating 4-byte trial decrypt."""
    out = bytearray(4)
    for i in range(4):
        b = (va + i) & 0xFF
        x = rol8(d[va + i], 2) ^ ((b + 1) & 0xFF)
        x = rol8(x, 2) ^ b
        out[i] = rol8(x, 2)
    return get_u32(out, 0)
```

16-byte descriptors throughout the loader are encrypted with `byte_rotate2`, chained positionally: each descriptor's key comes from its own address, and the walk terminates on a zero length field.
