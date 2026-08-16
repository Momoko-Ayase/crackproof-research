---
description: "LFSR 密钥流、导入名密码与稀疏页级代码变换。"
---

# LFSR、字符串与页变换

## LFSR 密钥流

按构建定制的字节码 stub（见下文）本身还包着一层 LFSR 密钥流。该流与数据无关——种子 1、反馈多项式 `0x8003`、每字节吐 8 位、LSB 优先——因此可在任意位置重放，这使得对候选 stub 位置做试解码代价很低：

```python
def lfsr_keystream(n):
    out = bytearray(n)
    state = 1
    for i in range(n):
        b = 0
        for k in range(8):
            b |= (state & 1) << k
            state = (state << 1) & MASK32
            if state & 0x8000:
                state ^= 0x8003
        out[i] = b
    return out

def lfsr_decrypt_block(d, pos):
    """XOR a bytecode stub with the keystream. The block length is stored
    unencrypted at pos+95."""
    length = d[pos + 95]
    ks = lfsr_keystream(length)
    for i in range(length):
        d[pos + i] ^= ks[i]
```

一个 stub 块占固定的 96 字节槽；`pos + 95` 处的字节是内部程序的（未加密）长度。

## 导入名字符串密码

DLL 名与导入函数名用一个滚动字节密码加密：半字节交换、减密钥、密钥步进 67。初始密钥是字符串 RVA 的低字节——不知道名字的位置就无法解密它。

```python
def string_cipher(d, pos, key):
    """Decrypt a NUL-terminated string in place."""
    i = 0
    while d[pos + i] != 0:
        b = ror8(d[pos + i], 4)
        b = (b - key) & 0xFF
        if b == 0:
            b = (-key) & 0xFF
        d[pos + i] = b
        key = (key + 67) & 0xFF
        i += 1
```

`b == 0` 的重映射避免在字符串中间产生 NUL（那会截断遍历）：若减法结果为零，该字节改为取密钥的二进制补码。

## 页级代码扰动

可执行节在一切之上还带一层稀疏的页粒度扰动：每 16 字节块 XOR 一个字节，块内偏移随块变化。模式跳过块 0（但其密钥状态仍推进）。每页 4096 字节中有 255 个被触及。

```python
def page_scramble(d, va, size, key):
    """64-bit form. `key` is the absolute page index shifted left by a
    build-specific amount (0 or 15)."""
    for i in range(size >> 4):
        mixed = (ror32(key, 15) + i) & MASK32
        key = (mixed + i) & MASK32
        if i == 0:
            continue
        d[va + i * 16 + (mixed & 0xF)] ^= key & 0xFF

def page_scramble_pe32(d, pa, page, big_formula):
    """32-bit form. The page key is (page+1) or 0x8000*(page+1)."""
    key = (0x8000 * (page + 1)) & MASK32 if big_formula else page + 1
    key = ror32(key, 15)
    for bi in range(1, 256):
        rk = ror32(key, 15)
        ri = (rk + bi) & MASK32
        key = (ri + bi) & MASK32
        d[pa + bi * 16 + (ri & 0xF)] ^= key & 0xFF
```

{% hint style="warning" %}
移位量（64 位：0 或 15）与公式选择（32 位：`page+1` 或 `0x8000*(page+1)`）**不记录在文件的任何字段里**。两个构建可以携带逐字节相同的配置戳却需要不同选择。唯一可靠的判别依据是代码内容本身：在每个候选下对采样页重放扰动，统计有多少位置解码为 `0xCC`（MSVC 的 `int3` 填充字节）。正确选择会不成比例地还原填充；错误选择则每 16 字节约搅乱 1 字节。某些模块（原生 DLL）代码是明文，绝不能做反扰动。
{% endhint %}

