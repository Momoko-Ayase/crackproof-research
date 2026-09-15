---
description: "Decode and validate the fixed-size outer header before reading the payload."
---

# Stage 1 header

The private `SHT_LOUSER` section isn't a single blob. Observed layout:

```
[0x23C-byte outer wrapper]
[0x1000-byte encrypted parameter area; only the first 32 bytes are the word header]
[encrypted stage 2 image]
[remaining record streams]
```

The observed default wrapper size is `0x23c` bytes (572 decimal). Two word-transform constants have been observed: `0xbf20165d` and `0xbf189bdd`. Each family uses one of them. Read the size and the constant from the private section when a build supplies a different value; the defaults are recognition clues, not universal assumptions.

How the stub finds that section at load time is described in [Stage 1 bootstrap](../runtime/stage1-bootstrap.md). The word cipher itself is on [Word, stream, and record ciphers](../data-transforms/word-and-record.md).

## Header fields

The decrypted word header contains eight 32-bit values:

| Field | Meaning | Required relation |
| --- | --- | --- |
| `key` | Per-file arithmetic key | Non-zero in observed files |
| `reserved` | Reserved word | Must be zero |
| `payload_offset` | File-relative payload start | Aligned and inside the private section |
| `payload_size` | Protected payload length | Non-zero and inside the section |
| `payload_key` | Key passed to the next stage | Preserved for stage 2 |
| `entry_offset` | Protected entry offset | Inside the recovered image range |
| `protect_size` | Range covered by protection | Doesn't exceed the image |
| `size_copy` | Copy of the payload length | Must equal `payload_size` |

The words are restored with unsigned 32-bit arithmetic. For word index `i`, the observed form is:

```
plain[i] = (cipher[i] + (i + 3) * key) XOR (C * (i + 1))
```

`C` is the family word constant. All intermediate values wrap at 32 bits. The first word supplies `key` and is written back after the 32-byte header is decrypted. Restore the complete header, then apply the field checks, rather than trusting a single decoded value. The remaining 0x1000 − 32 bytes of the parameter area aren't part of this eight-word table.

## Fail-closed checks

Reject the file when the header is truncated, the reserved word is non-zero, the copied size differs, the payload is unaligned or out of range, or the entry/protected ranges don't fit the image. These checks prevent random section data from being mistaken for a valid stream.
