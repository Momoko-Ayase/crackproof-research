---
description: "载荷滚动异或链、双字异或循环右移与三重字节循环移位算法。"
icon: rotate
---

# 滚动密钥与循环移位算法

各阶段头部与指针表使用四种基于 8 位和 32 位无符号回绕运算的原地解密算法。

{% hint style="success" %}
本页所有 Python 函数均由 `verification/verify_docs.py` 自动执行，并与独立参考测试向量逐字节比对校验。
{% endhint %}

## 通用位宽辅助函数

本页解密函数均在 `bytearray` 缓冲区上原地操作，并共用以下位运算与读写辅助函数：

```python
MASK32 = 0xFFFFFFFF

def get_u16(d, off):
    return d[off] | (d[off + 1] << 8)

def get_u32(d, off):
    return d[off] | (d[off + 1] << 8) | (d[off + 2] << 16) | (d[off + 3] << 24)

def put_u32(d, off, value):
    d[off:off + 4] = (value & MASK32).to_bytes(4, "little")

def rol32(x, n): return ((x << n) | (x >> (32 - n))) & MASK32
def ror32(x, n): return ((x >> n) | (x << (32 - n))) & MASK32
def rol8(x, n):  return ((x << n) | (x >> (8 - n))) & 0xFF
def ror8(x, n):  return ((x >> n) | (x << (8 - n))) & 0xFF
```

## 载荷滚动异或链

[容器布局与加密头部](../file-structure/container-layout.md)中的 `header_kdf` 与 `payload_xor_chain` 共用相同的下标平方反馈结构，区别在于此处使用 `+ i` 替代 `- i`，并以 `info[0] + ~decrypt_size` 作为初始种子：

```python
def payload_xor_chain(file_data, out, info, decrypt_size):
    """Decrypt the bulk of the payload into the image buffer."""
    base_src = (info[4] + 4096) & MASK32
    k = (info[0] + (~decrypt_size & MASK32)) & MASK32
    for i in range(decrypt_size >> 2):
        cell = get_u32(file_data, (base_src + 4 * i) & MASK32)
        put_u32(out, (info[3] + 4 * i) & MASK32, k ^ cell)
        k = (i * i) ^ ((k + cell + i) & MASK32)
```

由于滚动密钥 `k` 混入了每一个密文双字 `cell`，解密必须从 `i = 0` 开始，并传入准确的 `decrypt_size`（常规构建为 `info[6] - info[3] + 8192`，全载荷加密的紧凑 PE32 构建为 `info[5]`）。

## 双字异或循环右移算法（`dd3`）

`xor_ror_dwords` 先从 `pos` 读取 `{base_addr, length}`，随后将区间内的每个双字与 `key` 异或、循环右移 `shift` 位（64 位阶段为 `19` 或 `21`），再减去双字下标 `i`：

```python
def xor_ror_dwords(d, pos, key, shift):
    base_addr = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    for i in range(length >> 2):
        off = (base_addr + 4 * i) & MASK32
        v = get_u32(d, off) ^ key
        key = (key + i) & MASK32
        put_u32(d, off, (ror32(v, shift) - i) & MASK32)
```

PE32 构建的 `ThirdStage` 移位量随构建选自 `[19, 21, 17, 23, 15, 25, 13, 11]`；静态还原时依次试探这 8 个候选值，保留解密结果能通过后续阶段表结构校验的一项（详见[PE32、DLL 与无标记布局](../loading-and-pe-repair/loading/layout-variants.md)）。

## 三重字节循环移位算法（`dd4` 与 `dd5`）

这两个函数均对每个字节连续执行三次循环左移，并在相邻移位之间分别异或两个自增的密钥字节：

```python
def byte_rotate3(d, pos):
    """Descriptor-addressed variant: rotate by 3, keyed from the address."""
    base_addr = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    b = ((base_addr >> 8) + base_addr) & 0xFF
    b2 = (b + 1) & 0xFF
    for i in range(length):
        idx = base_addr + i
        x = rol8(d[idx], 3) ^ b2
        x = rol8(x, 3) ^ b
        d[idx] = rol8(x, 3)
        b = (b + 1) & 0xFF
        b2 = (b2 + 1) & 0xFF

def byte_rotate2(d, va, size):
    """Position-keyed variant: rotate by 2, keyed from the address itself."""
    b = va & 0xFF
    b2 = (b + 1) & 0xFF
    for i in range(size):
        idx = va + i
        x = rol8(d[idx], 2) ^ b2
        x = rol8(x, 2) ^ b
        d[idx] = rol8(x, 2)
        b = (b + 1) & 0xFF
        b2 = (b2 + 1) & 0xFF
```

在 `byte_rotate2` 中，偏移 `va + i` 处的明文字节仅取决于 `d[va + i]` 与 `(va + i) & 0xFF`，不依赖前序字节的状态传递，因此定位描述符表时可以直接做不修改原缓冲区的 4 字节试探解密：

```python
def trial_byte_rotate2(d, va):
    """Non-mutating 4-byte trial decrypt."""
    out = bytearray(4)
    for i in range(4):
        b = (va + i) & 0xFF
        x = rol8(d[va + i], 2) ^ ((b + 1) & 0xFF)
        x = rol8(x, 2) ^ b
        out[i] = rol8(x, 2)
    return get_u32(out, 0)
```

连续排列的 16 字节加载器描述符均按各自所在的 RVA 用 `byte_rotate2` 加密，并以 `length == 0` 作为序列结束标记。
