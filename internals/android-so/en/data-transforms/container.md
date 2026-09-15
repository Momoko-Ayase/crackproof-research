---
description: "Decode container descriptors, segment transforms, and raw or compressed writes."
---

# Container transforms

Module `0x9D` describes a container with a `0x5c`-byte [protected descriptor](word-and-record.md), a container header, a tree of records, and segment data. The descriptor gives the offsets and sizes needed to bound every later read. Seeds come from [module `0x9B`](module-config.md).

## Container header

The working seed is squared, then mixed. The second shift is 11, not 17:

```
s = (seed * seed) & MASK32
s = ((s >> 17) ^ (s << 11)) & MASK32
```

The next 12 bytes are three little-endian words. After `gf`:

| Word | Decodes to |
| --- | --- |
| `w0` | `gf(w0) + s*0xF87B337C + (0xA21DFB3A << (s & 7))`: total output size (0 means empty) |
| `w1` | `gf(w1) ^ (s + 0xBD19C63C + (0x416E2AF2 >> (s & 0xD)))`: low byte is the segment count; the next byte `== 1` skips AES |
| `w2` | `gf(w2) + (0x643A3A3B << (s & 0xB)) - (s ^ 0x3B2BF538)`: Huffman-table size |

A zero segment count or a table larger than `0x1B00` is rejected.

**Huffman table** (3-byte entries) starts at `+0x0C`. Each aligned dword is replaced by `gf` of itself, then a byte keystream is added:

```
k20 = (s + 0xF1CB5B81) * s
k21 = k20 - s * 0x23B32203
b[i] += (gf(k20 << (i & 0x1B)) - (k21 >> (i & 0x17))) >> (i & 0x1F)
```

**Segment table** starts at the 4-aligned end of the Huffman table. Each entry is `{offset, size}`. The dword keystream is:

```
k22 = ((s + 0xB31F451C) * s) << 3
s2  = k22 - s * 0x822FE82D
plain = gf(cipher ^ k22) + (s2 >> ((byte_offset & 7) + 5))
```

An offset/size pair that falls outside the `0x9D` record is rejected.

## Segment processing

Each segment is a word cipher, then an optional AES-256-CBC pass (zero IV) unless the header requested a skip, then a compressed block.

The word cipher uses a rolling `w0/w6/w7` state with a fixed constant set (`0x8e495673`, `0xe9fa57e4`, `0x72f6fcbe`, `0x4f8b1bca`, `0xb43b9baf`, `0xaf57f7fb`, `0x07b48238`, `0xe34eac63`). The scratch value `w7 ^ w6` overwrites `w0` and carries into the next iteration.

When AES runs, the schedule is the one recovered from module `0x9B` (14 rounds, marker `00 01 0e 00`). The decoder writes only to the declared target range.

The compressed-block stream starts with a 16-byte header `{base, count, table_offset, src_base}`, then `count` entries `{dst, out_len, src_len, pad}`. A write is a raw copy when `out_len == src_len`, otherwise a [compressed block](compression.md). For either form, the decoder requires:

1. source and target ranges inside the containing record;
2. exact source consumption; and
3. exact target length.

The tree may contain empty segments or metadata-only records. They're retained as records but don't create executable bytes. Overlap with a previously materialized range is rejected unless the record explicitly describes the same range and content.

A second container at the descriptor's auxiliary offset holds the relocation fixup database that replaced most of `.rela.dyn`. Observed records are 0x18 bytes `{u64 dst, u32 tag, u32 pad, u64 value}`. Tag `0x403` is an ABS64 pointer: the static image stores the virtual address `value` at `dst`. Other tags (`0x402` runs, `0x101`/`0x401` range descriptors) are retained as records but aren't required to produce a loadable ELF.
