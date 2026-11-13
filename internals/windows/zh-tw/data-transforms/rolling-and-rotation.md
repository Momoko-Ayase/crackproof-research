---
description: "滾動 XOR 負載鏈、XOR 右旋 dword 區塊與三重位元組旋轉加密。"
icon: rotate
---

# 滾動金鑰與旋轉加密

階段標頭與指標表採用四種小型原地（in-place）加密演算法，皆建立在 8 位元與 32 位元無號溢位回繞運算之上。

{% hint style="success" %}
本頁所有 Python 函式皆會由 `verification/verify_docs.py` 自動執行，並與獨立參考測試向量逐位元組比對驗證。
{% endhint %}

## 共用位元寬度輔助函式

以下所有函式皆直接在 `bytearray` 緩衝區上原地運算：

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

## 負載滾動 XOR 鏈

`payload_xor_chain` 與 `header_kdf`（見[容器結構與加密標頭](../file-structure/container-layout.md)）共用相同的索引平方回饋結構，但回饋項由 `- i` 改為 `+ i`，初始種子則為 `info[0] + ~decrypt_size`：

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

由於 `k` 每輪都會混入密文 dword `cell`，解密必須以精確的 `decrypt_size`（一般為 `info[6] - info[3] + 8192`，全負載加密的精簡型 PE32 組建則為 `info[5]`）從 `i = 0` 依序算起。

## XOR 與右旋 dword 加密（`dd3`）

`xor_ror_dwords` 會先從 `pos` 讀取 `{base_addr, length}`，接著將每個 dword 與 `key` 做 XOR、右旋 `shift` 位元（64 位元階段為 `19` 或 `21`），最後減去 dword 索引 `i`：

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

PE32 組建會對其中一個階段逐一測試 8 組候選旋轉位數 `[19, 21, 17, 23, 15, 25, 13, 11]`，並保留輸出能通過後續階段表驗證的那一組（詳見[PE32、專用 DLL 與無標記版型](../loading-and-pe-repair/loading/layout-variants.md)）。

## 三重位元組旋轉加密（`dd4` 與 `dd5`）

這兩種位元組轉換在解密時皆將每個位元組左旋三次，並在旋轉之間與兩個遞增的金鑰位元組做 XOR：

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

在 `byte_rotate2` 中，位址 `va + i` 的解密結果僅取決於 `d[va + i]` 與 `(va + i) & 0xFF`，不依賴前序位元組的狀態；因此在探索描述子表時，可不改動原緩衝區直接試解 4 位元組：

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

連續排列的 16 位元組載入器描述子陣列會在各項目自身的 RVA 處以 `byte_rotate2` 加密，並以 `length` 欄位為 `0` 的項目作為陣列結尾。
