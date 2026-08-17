---
description: CRC-32、三角數密鑰推進及連接受保護記錄的校驗和鏈。
---

# 校驗和與密鑰推進

## CRC-32 校驗和

校驗和使用標準反射 CRC-32（多項式 `0xEDB88320`，即 zlib/以太網 CRC——`crc32(b"123456789") == 0xCBF43926`）。出現兩種描述符形式：

```python
def _build_crc_table():
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = 0xEDB88320 ^ (c >> 1) if c & 1 else c >> 1
        table.append(c)
    return table

CRC_TABLE = _build_crc_table()

def crc32_append(initial, data):
    crc = ~initial & MASK32
    for b in data:
        crc = CRC_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return ~crc & MASK32

def crc32(data):
    return crc32_append(0, data)

def calculate_checksum(d, pos):
    """crc32(region) ^ length, where (offset, length) is read from d[pos]."""
    offset = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    return crc32(d[offset:offset + length]) ^ length
```

第二種形式以滾動初值鏈式覆蓋**原始文件字節**（用上一次結果作 `initial` 調用 `crc32_append`），用於[分階段加載器](../loading-and-pe-repair/loading/)中那條只用於校驗的遍歷。

## 三角數密鑰調度

若干階段密鑰通過累加結構化整數級數來“推進”——每輪把 1 到 `(m+1) * 100` 的每個整數都加上：

```python
def advance_key(key, iterations):
    for m in range(iterations):
        bound = ((m + 1) * 25) << 2
        for n in range(1, bound + 1):
            key = (key + n) & MASK32
    return key
```

種子是從剛解密的前一階段讀出的內容，所以只有之前的一切都解密正確，推進後的密鑰才會正確——這是防篡改設計的一半（另一半是本頁末尾的校驗和鏈）。

## 校驗和鏈

最後一個原語不是密碼，而是密鑰的組合方式。一個階段的解密密鑰通常形如：

```
stage_key = xor_accumulator ^ crc32_checksum_of_earlier_content ^ content_derived_seed
```

* **xor 累加器**：遍歷一張 `(offset, length)` 區域描述符表，把各項的 `calculate_checksum` 值異或累積。
* **校驗和**：對只有在前序階段正確解密後才以明文存在的字節做 CRC-32。
* **種子**：從剛解密的內容讀出的一個 dword，通常再經 `advance_key` 推進。

其結果是：各階段無法亂序解密；上游任何一字節被改動，下游由它派生的所有密鑰全部報廢。這條鏈是容器的防篡改機制——反過來，它也使得解包結果可驗證：任何一處選擇出錯，後續階段都解不開，而不是產生隱性的錯誤結果。各構建家族如何組合這些要素，正是下一頁的主題。
