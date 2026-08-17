---
description: Windows 载荷阶段使用的滚动 XOR、dword 旋转与字节旋转变换。
---

# 滚动密钥与旋转密码

容器的每一层都由一小组原语构成。一旦逐个定义清楚，分阶段加载器就只是“在偏移 X 处以密钥 Y 调用原语 N”的严格有序重复。本页精确定义每个原语，并给出 Python 实现。

{% hint style="success" %}
本页所有代码片段都已实际执行并与受保护二进制中实现的算法核对：每个函数的输出都在相同输入上与参考移植逐字节比对一致。
{% endhint %}

## 约定

所有缓冲区都是可变字节数组（`bytearray`）；原始算法原地工作。全文使用的辅助函数：

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

## 滚动密钥家族

两个密码共享同一滚动密钥设计：密钥从种子开始，每个单元与当前密钥异或，随后密钥混入单元值、循环索引与索引平方向前滚动。头部 KDF（见[受保护文件格式](../file-structure/file-format.md)）是 8 单元实例；payload 主体密码是同族的长形式，种子与更新规则不同：

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

由于密钥逐 dword 向前滚动，该链必须从头开始解——不重放整条链就无法对 payload 做随机访问。

## XOR + 循环右移 dword 密码

这个密码用于解开每个阶段的指针块。它从缓冲区自身读出 `(base_addr, length)` 描述符，然后变换每个 dword：与滚动密钥异或、按固定移位量循环右移、再减去循环索引。移位量按调用点取 19 或 21。

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

32 位构建还会对其中一个阶段在候选集 `[19, 21, 17, 23, 15, 25, 13, 11]` 上爆破移位量，接受输出能解析为合法阶段表的那个（见[分阶段加载器](../loading-and-pe-repair/loading/)）。

## 三重字节旋转密码

两个字节密码共享同一结构：每字节三次位旋转，旋转之间异或两个滚动密钥字节。它们的区别在于旋转量与初始密钥的派生方式。

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

位置密钥变体有一个加载器各表遍历重度依赖的性质：**每个输出字节只依赖输入字节与其地址的低 8 位**——无跨字节状态。因此任意 4 字节都可以在不触碰缓冲区其余部分的情况下试解：

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

加载器中贯穿始终的 16 字节描述符都用 `byte_rotate2` 加密，按位置串联：每个描述符的密钥来自其自身地址，遍历在长度字段为零时终止。
