---
description: "GF(2^32) 词混合、流首部与记录密码，以及 0x9D 受保护描述符。"
---

# 词、流与记录密码

Android 记录流不复用 Windows 的滚动 XOR 家族。词混合是 GF(2³²) 乘法。流首部、记录描述符和 `0x9D` 受保护描述符各自在这一乘法外包一层不同的反馈规则。常量随家族而变；本页的值是已观察材料，不是唯一通用密钥。

## GF(2³²) 乘法

`gf(w)` 在 GF(2³²) 上把 `w` 乘以固定元 `0x94511dd2`，约化多项式为 `0x579357eb`：

```python
MASK32 = 0xFFFFFFFF

def gf32_mul_fixed(value):
    multiplier = 0x94511DD2
    result = 0
    while multiplier:
        if multiplier & 1:
            result ^= value
        carry = value >> 31
        value = (value << 1) & 0xFFFFFFFF
        if carry:
            value ^= 0x579357EB
        multiplier >>= 1
    return result
```

本页后续公式以及[容器头](container.md)都调用此函数。

## 第一阶段词密码

32 字节参数头与第二阶段映像使用无符号 32 位回绕。对词下标 `i` 与家族常量 `C`：

```
plain[i] = (cipher[i] + (i + 3) * key) XOR (C * (i + 1))
```

已观察的 `C` 为 `0xbf20165d` 与 `0xbf189bdd`——每个家族用其中一个。第一个词是密钥，32 字节头解密后再写回去。字段检查见[第一阶段首部](../file-format/stage1.md)。

## 流首部密码

每个解释器流以两个小端 dword（`cipher0`、`cipher1`）开头。流标识（根上是 `0xE2`，随后 `0xE3`–`0xE8`）混入每流种子，再用来解密每条 `0x5c` 字节描述符。

已观察到两套常量。它们共享 `sid * 0x9D323CD7` 乘积和对首部词的 `gf` 混合；附加常量与移位组装不同。

**第一套已观察常量**

```
K = sid * 0x9D323CD7
K = ((K << (sid & 0xB)) + (K >> (sid & 7))) & 0xFFFFFFFF
dw0 = gf(cipher0 + 0xCBF0C1D8) ^ (K + 0x4178CB33)
dw1 = gf(cipher0 + cipher1)    ^ (K + 0xF119421B)
G   = (K + 0x5590AD79 + dw1) & 0xFFFFFFFF
```

**第二套已观察常量**

```
K    = sid * 0x9D323CD7
mix  = (K >> (sid & 7)) + 0x5E727D74
mix  = (mix + (K << (sid & 0xB)) + 0xF71E3005) & 0xFFFFFFFF
dw0  = gf(cipher0 + 0xCBF0C1D8) ^ (0xEBE81DBA + mix)
dw1  = gf(cipher1 + cipher0)    ^ (0xEBE81DBA * 5 + mix)
G    = (dw1 + mix) & 0xFFFFFFFF
```

`G` 是该整条流的描述符密码种子。无论构建使用哪套常量，[第二阶段记录流](../file-format/stage2-streams.md)中的结构检查都仍然有效。

## 记录描述符密码

每条 0x5c 字节描述符是 23 个小端 dword。一旦知道 `G`，两套家族的遍历相同：

```python
def rec_decrypt(G, idx, rec):
    product = ((G + 0x96F60B71) * G) & MASK32
    record_mask = (product << ((idx + 1) & 3)) & MASK32
    stream_mix = (G * 0x06A55BCC + product) & MASK32
    feedback = 0xF02F7685
    acc = 0x79934CF6
    for off in range(0, 0x5C, 4):
        cipher = get_u32(rec, off)
        square = (feedback * feedback) & MASK32
        value = gf32_mul_fixed(cipher ^ (square >> 3))
        value = (value ^ record_mask) & MASK32
        value = (value + acc + G) & MASK32
        value = (value - (stream_mix >> ((off + 3) & 5))) & MASK32
        put_u32(rec, off, value)
        acc = (acc + 0xE64D33D8) & MASK32
        feedback = cipher
```

`(off + 3) & 5` 是按位与，不是常量 3：第 0 词移 1、第 1 词移 5，随后交替。把它读成常量 3 会静默解出垃圾。`G` 对整条流恒定；`idx` 改变每条描述符的 `record_mask`；`feedback` 携带前一个*密文*词。

## `0x9D` 受保护描述符

模块 `0x9D` 以另一条 0x5c 字节记录开头，用配置模块的首部种子 `S` 再加密：

```python
def decrypt_protected_descriptor(data, seed):
    base0 = ((seed + 0xD3E87144) * seed) & MASK32
    base1 = (base0 + seed * 0x0BD9418D) & MASK32
    words = [0] * (0x5C // 4)
    for i in range(len(words)):
        cipher = get_u32(data, i * 4)
        sub = (base0 << (4 if i & 1 else 0)) & MASK32
        words[i] = ((cipher - sub) ^ (base1 >> ((seed + i * 4) & 7))) & MASK32
    return words
```

已观察明文：`command_id == 0x9D`、`outer_offset == 0x5C`，前六个词之后的保留词为零。这六个词给出外层容器的偏移/大小，以及[容器变换](container.md)所用辅助（重定位）容器的偏移/大小。
