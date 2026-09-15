---
description: "GF(2^32) 詞混合、流首部與記錄密碼，以及 0x9D 受保護描述符。"
---

# 詞、流與記錄密碼

Android 記錄流不復用 Windows 的滾動 XOR 家族。詞混合是 GF(2³²) 乘法。流首部、記錄描述符和 `0x9D` 受保護描述符各自在這一乘法外包一層不同的反饋規則。常量隨家族而變；本頁的值是已觀察材料，不是唯一通用密鑰。

## GF(2³²) 乘法

`gf(w)` 在 GF(2³²) 上把 `w` 乘以固定元 `0x94511dd2`，約化多項式為 `0x579357eb`：

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

本頁後續公式以及[容器頭](container.md)都調用此函數。

## 第一階段詞密碼

32 字節參數頭與第二階段映像使用無符號 32 位迴繞。對詞下標 `i` 與家族常量 `C`：

```
plain[i] = (cipher[i] + (i + 3) * key) XOR (C * (i + 1))
```

已觀察的 `C` 為 `0xbf20165d` 與 `0xbf189bdd`——每個家族用其中一個。第一個詞是密鑰，32 字節頭解密後再寫回去。字段檢查見[第一階段首部](../file-format/stage1.md)。

## 流首部密碼

每個解釋器流以兩個小端 dword（`cipher0`、`cipher1`）開頭。流標識（根上是 `0xE2`，隨後 `0xE3`–`0xE8`）混入每流種子，再用來解密每條 `0x5c` 字節描述符。

已觀察到兩套常量。它們共享 `sid * 0x9D323CD7` 乘積和對首部詞的 `gf` 混合；附加常量與移位組裝不同。

**第一套已觀察常量**

```
K = sid * 0x9D323CD7
K = ((K << (sid & 0xB)) + (K >> (sid & 7))) & 0xFFFFFFFF
dw0 = gf(cipher0 + 0xCBF0C1D8) ^ (K + 0x4178CB33)
dw1 = gf(cipher0 + cipher1)    ^ (K + 0xF119421B)
G   = (K + 0x5590AD79 + dw1) & 0xFFFFFFFF
```

**第二套已觀察常量**

```
K    = sid * 0x9D323CD7
mix  = (K >> (sid & 7)) + 0x5E727D74
mix  = (mix + (K << (sid & 0xB)) + 0xF71E3005) & 0xFFFFFFFF
dw0  = gf(cipher0 + 0xCBF0C1D8) ^ (0xEBE81DBA + mix)
dw1  = gf(cipher1 + cipher0)    ^ (0xEBE81DBA * 5 + mix)
G    = (dw1 + mix) & 0xFFFFFFFF
```

`G` 是該整條流的描述符密碼種子。無論構建使用哪套常量，[第二階段記錄流](../file-format/stage2-streams.md)中的結構檢查都仍然有效。

## 記錄描述符密碼

每條 0x5c 字節描述符是 23 個小端 dword。一旦知道 `G`，兩套家族的遍歷相同：

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

`(off + 3) & 5` 是按位與，不是常量 3：第 0 詞移 1、第 1 詞移 5，隨後交替。把它讀成常量 3 會靜默解出垃圾。`G` 對整條流恆定；`idx` 改變每條描述符的 `record_mask`；`feedback` 攜帶前一個*密文*詞。

## `0x9D` 受保護描述符

模塊 `0x9D` 以另一條 0x5c 字節記錄開頭，用配置模塊的首部種子 `S` 再加密：

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

已觀察明文：`command_id == 0x9D`、`outer_offset == 0x5C`，前六個詞之後的保留詞為零。這六個詞給出外層容器的偏移/大小，以及[容器變換](container.md)所用輔助（重定位）容器的偏移/大小。
