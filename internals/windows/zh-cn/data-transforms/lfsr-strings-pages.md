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
移位量（64 位：0 或 15）与公式选择（32 位：`page+1` 或 `0x8000*(page+1)`）**不记录在文件的任何字段里**。两个构建可以携带逐字节相同的配置戳却需要不同选择。第三种结果同样必须考虑：保持字节不变。原生 DLL 的 `.text` 常常本就是明文；对它套任一公式仍会每 16 字节 XOR 约 1 字节。

在 64 位映像上，可识别的 CRT 入口 stub 比填充统计更强。常见形状是 `48 83 EC ib / E8 rel32 / 48 83 C4 ib / E9 rel32`（两处栈立即数相同）。只有当某个候选——包括“不变换”——是唯一一个让解码后的 `call` 与 `jmp` 目标都落在 `.text` 内的选择时，才接受它。入口代码无法识别时退回填充统计：在采样页上重放各移位，统计变成 `0xCC` 的位置。必须相对未改字节既有倍率优势，也有绝对下限。小幅增长是每页 XOR 255 个伪随机位置的噪声，不能据此执行变换。

在 32 位映像上，同一套 `0xCC` 比较在 `page+1` 与 `0x8000*(page+1)` 之间选择，并在两种公式都无法把填充数明显抬过未改基线时跳过该遍。
{% endhint %}

