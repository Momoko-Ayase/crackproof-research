---
description: "Huffman/LZ 混合解压器：3 字节表项，字面量/行程填充/回溯引用令牌。"
---

# huffman.py

用于 stage 与节数据块的解压器，见 [Huffman 与 LZ 压缩](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/shu-ju-bian-huan/data-transforms/compression)。

```python
"""The Huffman/LZ hybrid decompressor.

Compressed blocks carry their own decoding table at `key_offset` in the same
buffer. The table is a forest of 3-byte entries:

    +0  u16  symbol / child index
    +2  u8   accumulated code length in bits

Root selection reads 8 bits (entry index = next 8 bits of input). An entry
with the top bit (0x8000) set is a leaf: the low 15 bits are the token. A
clear top bit means an internal node: the low 15 bits are the index of the
first of a sibling pair, and one more input bit picks between them. The
stored length byte counts the bits consumed so far (8 for a root), so a
leaf reached after walking N internal levels has a total code length of
8 + N bits.

Each token has a mode in its bits 8-9 and a payload in bits 0-7:

    0x000  literal: emit the payload byte
    0x100  count accumulator: append the payload to a big-endian pending
           value (emits nothing by itself)
    0x200  run fill: repeat the previously written 1/2/4-byte unit
           pending * payload times
    0x300  LZ back-reference: copy `payload` bytes from
           (pending + payload) bytes behind the output cursor
"""


def get_u16(d, off):
    return d[off] | (d[off + 1] << 8)


def get_u32(d, off):
    return d[off] | (d[off + 1] << 8) | (d[off + 2] << 16) | (d[off + 3] << 24)


def put_u16(d, off, value):
    d[off:off + 2] = (value & 0xFFFF).to_bytes(2, "little")


def put_u32(d, off, value):
    d[off:off + 4] = (value & 0xFFFFFFFF).to_bytes(4, "little")


def decompress(d, src, dest, key_offset, s_size, d_size):
    """Decompress s_size bytes at `src` into d_size bytes at `dest`,
    in place within buffer `d`. Returns True when exactly d_size bytes
    were produced."""
    bit_pos = 0
    buf = bytearray(d[src:src + s_size]) + bytearray(3)  # 3 bytes of slack
    buf_off = 0
    src_consumed = 0
    pending = 0
    written = 0

    while src_consumed < s_size and written < d_size:
        word = get_u32(buf, buf_off) >> bit_pos
        tab_addr = key_offset + (word & 0xFF) * 3
        tab = get_u16(d, tab_addr)
        if tab & 0x8000:  # leaf: token is in the low 15 bits
            tab &= 0x7FFF
            bits = d[tab_addr + 2]
        else:  # internal node: walk down one bit per level
            bits = d[tab_addr + 2]
            if bits >= 32:
                return False
            mask = 1 << bits
            bits += 1
            idx = (tab & 0x7FFF) + (1 if word & mask else 0)
            t2 = get_u16(d, key_offset + idx * 3)
            depth = 0
            while not (t2 & 0x8000):
                depth += 1
                if depth > 64:
                    return False
                mask <<= 1
                bits += 1
                idx = (t2 & 0x7FFF) + (1 if word & mask else 0)
                t2 = get_u16(d, key_offset + idx * 3)
            tab = t2 & 0x7FFF

        bit_pos += bits
        advance = bit_pos // 8
        buf_off += advance
        src_consumed += advance
        bit_pos %= 8

        mode = tab & 0x300
        payload = tab & 0xFF
        if mode == 0x000:  # literal
            step = 1
            d[dest] = payload
        elif mode == 0x100:  # count accumulator
            step = 0
            if pending >= 256:
                return False
            pending = payload if pending == 0 else (pending << 8) | payload
        elif mode == 0x200:  # run fill
            if pending == 0:
                pending = 1
            step = pending * payload
            if step + written > d_size:
                return False
            if payload == 1:
                if dest < 1:
                    return False
                v = d[dest - 1]
                for k in range(pending):
                    d[dest + k] = v
            elif payload == 2:
                if dest < 2:
                    return False
                v = get_u16(d, dest - 2)
                for k in range(pending):
                    put_u16(d, dest + k * 2, v)
            elif payload == 4:
                if dest < 4:
                    return False
                v = get_u32(d, dest - 4)
                for k in range(pending):
                    put_u32(d, dest + k * 4, v)
            else:
                return False
            pending = 0
        else:  # 0x300: LZ back-reference
            step = payload
            if written + payload > d_size or pending + payload > written:
                return False
            back = pending + payload
            for k in range(payload):
                d[dest + k] = d[dest + k - back]
            pending = 0

        dest += step
        written += step
        if bits == 0 and step == 0:
            return False

    return written == d_size
```
