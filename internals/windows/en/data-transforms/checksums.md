---
description: "CRC-32, triangular key progression, and the checksum chain that links protected records."
---

# Checksums and key progression

## CRC-32 checksums

Checksums use the standard reflected CRC-32 (polynomial `0xEDB88320`, the zlib/Ethernet CRC — `crc32(b"123456789") == 0xCBF43926`). Two descriptor forms appear:

```python
def _build_crc_table():
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = 0xEDB88320 ^ (c >> 1) if c & 1 else c >> 1
        table.append(c)
    return table

CRC_TABLE = _build_crc_table()

def crc32_append(initial, data):
    crc = ~initial & MASK32
    for b in data:
        crc = CRC_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return ~crc & MASK32

def crc32(data):
    return crc32_append(0, data)

def calculate_checksum(d, pos):
    """crc32(region) ^ length, where (offset, length) is read from d[pos]."""
    offset = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    return crc32(d[offset:offset + length]) ^ length
```

A second form chains over the **original file bytes** with a running initial value (`crc32_append` with the previous result as `initial`), used by the validation-only walk described in [The staged loader](../loading-and-pe-repair/loading/README.md).

## The triangular key schedule

Several stage keys are "advanced" by adding structured integer series — each iteration adds every integer from 1 to `(m+1) * 100`:

```python
def advance_key(key, iterations):
    for m in range(iterations):
        bound = ((m + 1) * 25) << 2
        for n in range(1, bound + 1):
            key = (key + n) & MASK32
    return key
```

The seed is content read from the previously decrypted stage, so the advanced key only comes out right when everything before it decrypted correctly — one half of the tamper-evidence design (the other half is the checksum chain at the end of this page).

## The checksum chain

The last primitive is not a cipher but the way keys are composed. A stage's decryption key is typically:

```
stage_key = xor_accumulator ^ crc32_checksum_of_earlier_content ^ content_derived_seed
```

- The **xor accumulator** is built by walking a table of `(offset, length)` region descriptors and XORing their `calculate_checksum` values.
- The **checksums** are CRC-32 over bytes that only exist in plaintext after the preceding stages decrypted correctly.
- The **seed** is a dword read from freshly decrypted content, usually advanced with `advance_key`.

The consequence: stages cannot be decrypted out of order, and any byte modified anywhere upstream corrupts every key derived from it downstream. The chain is the container's tamper-evidence mechanism — and, inverted, it is also what makes an unpacked image verifiable: a single wrong choice anywhere leaves later stages undecryptable rather than subtly wrong. How each build family composes these ingredients is the subject of the next page.

