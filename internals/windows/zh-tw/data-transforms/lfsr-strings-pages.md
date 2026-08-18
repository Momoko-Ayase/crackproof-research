---
description: "LFSR 密鑰流、導入名密碼與稀疏頁級代碼變換。"
---

# LFSR、字符串與頁變換

## LFSR 密鑰流

按構建定製的字節碼 stub（見下文）本身還包著一層 LFSR 密鑰流。該流與數據無關——種子 1、反饋多項式 `0x8003`、每字節吐 8 位、LSB 優先——因此可在任意位置重放，這使得對候選 stub 位置做試解碼代價很低：

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

一個 stub 塊佔固定的 96 字節槽；`pos + 95` 處的字節是內部程序的（未加密）長度。

## 導入名字符串密碼

DLL 名與導入函數名用一個滾動字節密碼加密：半字節交換、減密鑰、密鑰步進 67。初始密鑰是字符串 RVA 的低字節——不知道名字的位置就無法解密它。

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

`b == 0` 的重映射避免在字符串中間產生 NUL（那會截斷遍歷）：若減法結果為零，該字節改為取密鑰的二進制補碼。

## 頁級代碼擾動

可執行節在一切之上還帶一層稀疏的頁粒度擾動：每 16 字節塊 XOR 一個字節，塊內偏移隨塊變化。模式跳過塊 0（但其密鑰狀態仍推進）。每頁 4096 字節中有 255 個被觸及。

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
移位量（64 位：0 或 15）與公式選擇（32 位：`page+1` 或 `0x8000*(page+1)`）**不記錄在文件的任何字段裡**。兩個構建可以攜帶逐字節相同的配置戳卻需要不同選擇。第三種結果同樣必須考慮：保持字節不變。原生 DLL 的 `.text` 常常本就是明文；對它套任一公式仍會每 16 字節 XOR 約 1 字節。

在 64 位映像上，可識別的 CRT 入口 stub 比填充統計更強。常見形狀是 `48 83 EC ib / E8 rel32 / 48 83 C4 ib / E9 rel32`（兩處棧立即數相同）。只有當某個候選——包括“不變換”——是唯一一個讓解碼後的 `call` 與 `jmp` 目標都落在 `.text` 內的選擇時，才接受它。入口代碼無法識別時退回填充統計：在採樣頁上重放各移位，統計變成 `0xCC` 的位置。必須相對未改字節既有倍率優勢，也有絕對下限。小幅增長是每頁 XOR 255 個偽隨機位置的噪聲，不能據此執行變換。

在 32 位映像上，同一套 `0xCC` 比較在 `page+1` 與 `0x8000*(page+1)` 之間選擇，並在兩種公式都無法把填充數明顯抬過未改基線時跳過該遍。
{% endhint %}

