---
description: "Decode and validate the fixed-size outer header before reading the payload."
---

# Stage 1 header

The first stage uses a fixed-size parameter area. The observed default outer size is `0x23c` bytes and the word transform uses the constant `0xbf20165d`. Implementations must read the size from the protected section when a build supplies a different value; the defaults are recognition clues, not universal assumptions.

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
| `protect_size` | Range covered by protection | Does not exceed the image |
| `size_copy` | Copy of the payload length | Must equal `payload_size` |

The words are restored with unsigned 32-bit arithmetic. For word index `i`, the observed form is:

```
plain[i] = (cipher[i] + (i + 3) * key) XOR (0xbf20165d * (i + 1))
```

All intermediate values wrap at 32 bits. The first word supplies `key`; implementations should restore the complete header and then apply the field checks rather than trusting a single decoded value.

## Fail-closed checks

Reject the file when the header is truncated, the reserved word is non-zero, the copied size differs, the payload is unaligned or out of range, or the entry/protected ranges do not fit the image. These checks prevent random section data from being mistaken for a valid stream.
