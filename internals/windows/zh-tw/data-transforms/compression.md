---
description: 壓縮節記錄所用的 Huffman 與 LZ 組合流格式。
---

# Huffman 與 LZ 壓縮

## Huffman/LZ 壓縮格式

多數 payload 塊用一種定製混合格式壓縮：Huffman 編碼的 token 流，token 分字面量、遊程填充與 LZ 回拷三類。解碼錶隨數據同行，位於同一緩衝區的 `key_offset` 處。

**表格式。** 表是 3 字節表項構成的森林：一個 u16 符號/子節點字段與一個 u8 碼長字段。根選擇讀 8 位輸入作為表項索引。最高位（`0x8000`）標記葉子；內部節點存儲兄弟節點對中首個的索引，再多讀 1 位輸入在二者間選擇。存儲的長度字節累計迄今消耗的位數（根為 8），因此走過 N 層內部節點到達的葉子，其總碼長為 8 + N 位。

**token 格式。** token 的 8–9 位選擇模式，0–7 位是載荷：

| 模式      | 含義                                                  |
| ------- | --------------------------------------------------- |
| `0x000` | 字面量：輸出載荷字節                                          |
| `0x100` | 計數累加器：把載荷拼進一個大端 pending 值（本身不輸出）                    |
| `0x200` | 遊程填充：把剛寫出的 1/2/4 字節單元重複 `pending × payload` 次       |
| `0x300` | LZ 回拷：從輸出遊標前 `pending + payload` 字節處拷貝 `payload` 字節 |

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

布爾返回值是損壞信號，也提供了明確的校驗條件：當容器沒有記錄某個密鑰或移位選擇時，就逐個嘗試候選，直到某個能乾淨解壓為止。[分階段加載器](../loading-and-pe-repair/loading/)中有多處這樣的“試解-驗證”點。
