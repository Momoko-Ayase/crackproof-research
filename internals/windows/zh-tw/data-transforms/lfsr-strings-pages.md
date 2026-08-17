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
移位量（64 位：0 或 15）與公式選擇（32 位：`page+1` 或 `0x8000*(page+1)`）**不記錄在文件的任何字段裡**。兩個構建可以攜帶逐字節相同的配置戳卻需要不同選擇。唯一可靠的判別依據是代碼內容本身：在每個候選下對採樣頁重放擾動，統計有多少位置解碼為 `0xCC`（MSVC 的 `int3` 填充字節）。正確選擇會不成比例地還原填充；錯誤選擇則每 16 字節約攪亂 1 字節。某些模塊（原生 DLL）代碼是明文，絕不能做反擾動。
{% endhint %}

