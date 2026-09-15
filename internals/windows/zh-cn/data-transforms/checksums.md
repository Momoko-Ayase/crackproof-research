---
description: CRC-32、三角数密钥推进及连接受保护记录的校验和链。
---

# 校验和与密钥推进

## CRC-32 校验和

校验和使用标准反射 CRC-32（多项式 `0xEDB88320`，即 zlib/以太网 CRC——`crc32(b"123456789") == 0xCBF43926`）。出现两种描述符形式：

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

第二种形式以滚动初值链式覆盖**原始文件字节**（用上一次结果作 `initial` 调用 `crc32_append`），用于[加载与节恢复](../loading-and-pe-repair/loading/README.md)中那条只用于校验的遍历。

## 三角数密钥调度

若干阶段密钥通过累加结构化整数级数来“推进”——每轮把 1 到 `(m+1) * 100` 的每个整数都加上：

```python
def advance_key(key, iterations):
    for m in range(iterations):
        bound = ((m + 1) * 25) << 2
        for n in range(1, bound + 1):
            key = (key + n) & MASK32
    return key
```

种子是从刚解密的前一阶段读出的内容，所以只有之前的一切都解密正确，推进后的密钥才会正确。这是防篡改设计的一半；另一半是[校验和链](#校验和链)。

## 校验和链

最后一个原语不是密码，而是密钥的组合方式。一个阶段的解密密钥通常形如：

```
stage_key = xor_accumulator ^ crc32_checksum_of_earlier_content ^ content_derived_seed
```

* **xor 累加器**：遍历一张 `(offset, length)` 区域描述符表，把各项的 `calculate_checksum` 值异或累积。
* **校验和**：对只有在前序阶段正确解密后才以明文存在的字节做 CRC-32。
* **种子**：从刚解密的内容读出的一个 dword，通常再经 `advance_key` 推进。

其结果是：各阶段无法乱序解密；上游任何一字节被改动，下游由它派生的所有密钥全部报废。这条链是容器的防篡改机制。反过来，它也表明重建映像是否自洽：任何一处选择出错，后续阶段都解不开，而不是产生隐性的错误结果。[阶段链与标记布局](../loading-and-pe-repair/loading/stage-chain.md)说明各构建家族如何组合这些要素。
