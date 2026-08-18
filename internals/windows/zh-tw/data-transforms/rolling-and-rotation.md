---
description: Windows 載荷階段使用的滾動 XOR、dword 旋轉與字節旋轉變換。
---

# 滾動密鑰與旋轉密碼

容器的每一層都由一小組原語構成。一旦逐個定義清楚，分階段加載器就只是“在偏移 X 處以密鑰 Y 調用原語 N”的嚴格有序重複。本頁精確定義每個原語，並給出 Python 實現。

{% hint style="success" %}
本頁所有代碼片段都已實際執行並與受保護二進制中實現的算法核對：每個函數的輸出都在相同輸入上與參考移植逐字節比對一致。
{% endhint %}

## 約定

所有緩衝區都是可變字節數組（`bytearray`）；原始算法原地工作。全文使用的輔助函數：

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

## 滾動密鑰家族

兩個密碼共享同一滾動密鑰設計：密鑰從種子開始，每個單元與當前密鑰異或，隨後密鑰混入單元值、循環索引與索引平方向前滾動。頭部 KDF（見[容器與加密頭](../file-structure/container-layout.md)）是 8 單元實例；payload 主體密碼是同族的長形式，種子與更新規則不同：

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

由於密鑰逐 dword 向前滾動，該鏈必須從頭開始解——不重放整條鏈就無法對 payload 做隨機訪問。

## XOR + 循環右移 dword 密碼

這個密碼用於解開每個階段的指針塊。它從緩衝區自身讀出 `(base_addr, length)` 描述符，然後變換每個 dword：與滾動密鑰異或、按固定移位量循環右移、再減去循環索引。移位量按調用點取 19 或 21。

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

32 位構建還會對其中一個階段在候選集 `[19, 21, 17, 23, 15, 25, 13, 11]` 上爆破移位量，接受輸出能解析為合法階段表的那個（見[加載與節恢復](../loading-and-pe-repair/loading/)）。

## 三重字節旋轉密碼

兩個字節密碼共享同一結構：每字節三次位旋轉，旋轉之間異或兩個滾動密鑰字節。它們的區別在於旋轉量與初始密鑰的派生方式。

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

位置密鑰變體有一個加載器各表遍歷重度依賴的性質：**每個輸出字節只依賴輸入字節與其地址的低 8 位**——無跨字節狀態。因此任意 4 字節都可以在不觸碰緩衝區其餘部分的情況下試解：

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

加載器中貫穿始終的 16 字節描述符都用 `byte_rotate2` 加密，按位置串聯：每個描述符的密鑰來自其自身地址，遍歷在長度字段為零時終止。
