---
description: "The Huffman and LZ writer format and the checks needed for safe expansion."
---

# Huffman and LZ compression

Compressed blocks use a compact Huffman table followed by an LZ-style stream. The table is a forest of 3-byte entries: a u16 symbol/child field and a u8 code-length field. Eight input bits select the root. The high bit (`0x8000`) marks a leaf; internal nodes store the index of the first of a sibling pair, and one more input bit chooses between them.

This is the same token language as the [Windows Huffman/LZ format](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/data-transforms/compression). A 16-bit prefix lookup can accelerate the first bits of a code; longer codes walk the tree.

**Token format.** Bits 8–9 select the mode, bits 0–7 are the payload:

| Mode | Meaning |
| --- | --- |
| `0x000` | Literal: emit the payload byte |
| `0x100` | Count accumulator: append the payload to a big-endian pending value (emits nothing by itself) |
| `0x200` | Run fill: repeat the previously written 1/2/4-byte unit `pending × payload` times |
| `0x300` | LZ back-reference: copy `payload` bytes from `pending + payload` bytes behind the output cursor |

A pair is valid only when the distance is non-zero, doesn't point before the beginning of output, and doesn't make the requested length exceed the declared target. Unit widths other than 1, 2, or 4 are a format error: the decoder must not count those bytes as written. One lab note records a skip-run sub-case for unusual widths; that behavior hasn't been reproduced in the cross-build decoder and isn't part of the accepted format.

The block is valid only when the bit reader consumes the permitted input and the output reaches the exact declared size. An early end marker, a dangling tree index, a zero-width leaf, or trailing bytes outside the documented padding is a format error rather than a partial success.
