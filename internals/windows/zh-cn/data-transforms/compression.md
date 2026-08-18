---
description: 压缩节记录所用的 Huffman 与 LZ 组合流格式。
---

# Huffman 与 LZ 压缩

## Huffman/LZ 压缩格式

多数 payload 块用一种定制混合格式压缩：Huffman 编码的 token 流，token 分字面量、游程填充与 LZ 回拷三类。解码表随数据同行，位于同一缓冲区的 `key_offset` 处。

**表格式。** 表是 3 字节表项构成的森林：一个 u16 符号/子节点字段与一个 u8 码长字段。根选择读 8 位输入作为表项索引。最高位（`0x8000`）标记叶子；内部节点存储兄弟节点对中首个的索引，再多读 1 位输入在二者间选择。存储的长度字节累计迄今消耗的位数（根为 8），因此走过 N 层内部节点到达的叶子，其总码长为 8 + N 位。

**token 格式。** token 的 8–9 位选择模式，0–7 位是载荷：

| 模式      | 含义                                                  |
| ------- | --------------------------------------------------- |
| `0x000` | 字面量：输出载荷字节                                          |
| `0x100` | 计数累加器：把载荷拼进一个大端 pending 值（本身不输出）                    |
| `0x200` | 游程填充：把刚写出的 1/2/4 字节单元重复 `pending × payload` 次       |
| `0x300` | LZ 回拷：从输出游标前 `pending + payload` 字节处拷贝 `payload` 字节 |

```python
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
        if tab & 0x8000:  # leaf
            tab &= 0x7FFF
            bits = d[tab_addr + 2]
        else:             # internal node: walk down one bit per level
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

布尔返回值是损坏信号，也提供了明确的校验条件：当容器没有记录某个密钥或移位选择时，就逐个尝试候选，直到某个能干净解压为止。[加载与节恢复](../loading-and-pe-repair/loading/)中有多处这样的“试解-验证”点。同一套 token 类别与 3 字节 Huffman 项也出现在 [Android 原生库格式](https://app.gitbook.com/s/Aoyn9wKiHAVzBKGSUifa/data-transforms/compression)中。
