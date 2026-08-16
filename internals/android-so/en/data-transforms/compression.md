---
description: "The Huffman and LZ writer format and the checks needed for safe expansion."
---

# Huffman and LZ compression

Compressed writer blocks use a compact Huffman table followed by an LZ-style stream. Huffman nodes are three bytes each; the high bit distinguishes a leaf from a child index. A 16-bit lookup table accelerates the first bits of a code, then the tree is followed for longer codes.

Decoded symbols are either literals or length/distance pairs. A pair copies already-produced bytes from the output window. The decoder checks that the distance is non-zero, does not point before the beginning of output, and does not make the requested length exceed the declared target.

The block is valid only when the bit reader consumes the permitted input and the output reaches the exact declared size. An early end marker, a dangling tree index, or trailing bytes outside the documented padding is a format error rather than a partial success.
