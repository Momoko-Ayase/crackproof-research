---
description: "Rolling XOR payload chains, XOR-and-rotate dword blocks, and triple byte-rotation ciphers."
icon: rotate
---

# Rolling-key and rotation ciphers

Stage headers and pointer tables use four small in-place ciphers built on 8-bit and 32-bit unsigned wraparound.

{% hint style="success" %}
Every Python function on this page is executed automatically by `verification/verify_docs.py` and checked byte-for-byte against independent reference test vectors.
{% endhint %}

## Shared bit-width helpers

All functions operate on mutable `bytearray` buffers in place:

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

## Payload rolling XOR chain

`header_kdf` (on [Container and encrypted header](../file-structure/container-layout.md)) and `payload_xor_chain` share the same index-squared feedback structure with `+ i` instead of `- i` and seed `info[0] + ~decrypt_size`:

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

Because `k` incorporates every ciphertext dword `cell`, decryption must start at `i = 0` with the exact `decrypt_size` (`info[6] - info[3] + 8192`, or `info[5]` on full-payload compact PE32 builds).

## XOR and rotate-right dword cipher (`dd3`)

This primitive reads `{base_addr, length}` at `pos`, then XORs each dword with `key`, rotates right by `shift` (`19` or `21` on 64-bit stages), and subtracts dword index `i`:

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

PE32 builds trial-decrypt one stage across the eight-shift candidate list `[19, 21, 17, 23, 15, 25, 13, 11]` and keep the shift whose output passes downstream stage-table validation (see [PE32, DLL, and marker-less layouts](../loading-and-pe-repair/loading/layout-variants.md)).

## Triple byte-rotation ciphers (`dd4` and `dd5`)

Both byte ciphers rotate each byte left three times with two incrementing key bytes XORed between rotations:

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

In `byte_rotate2`, byte `va + i` depends solely on `d[va + i]` and `(va + i) & 0xFF` with no carry from previous bytes, allowing non-destructive 4-byte lookahead during descriptor-table discovery:

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

Chained 16-byte loader descriptors are encrypted under `byte_rotate2` at their own RVAs and terminate on a zero `length` field.
