---
description: "0x8003 LFSR 存根加密、RVA 匯入名稱字串加密與逐頁 .text 程式碼擾碼。"
icon: wave-square
---

# LFSR、字串與分頁轉換

## LFSR 金鑰流（`dd6`） <a href="#lfsr-keystream-dd6" id="lfsr-keystream-dd6"></a>

每個 96 位元組的[隨組建位元組碼存根](bytecode-transform.md)槽位會在 `pos + 95` 存放未加密的程式長度（`<= 95`），並以固定種子的 Galois LFSR（初始狀態 `1`、多項式 `0x8003`，每個位元組由最低有效位元起依序輸出 8 位元）遮罩 `d[pos .. pos + length]`：

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

由於金鑰流僅取決於位元組相對位移 `0..length`，掃描時只需預先算好一份 95 位元組的金鑰流表，即可在任意位移測試 96 位元組的候選視窗。

## 匯入名稱字串加密（`dd7`）

加密的 DLL 名稱與匯入符號名稱皆以 NUL 結尾；解密時逐位元組交換高低半位元組（`ror8(..., 4)`）並減去 `key`，若結果為 `0` 則還原為 `(-key) & 0xFF`（加密端藉此避開會在密文中產生 `0x00` 而提前截斷字串的值），最後將 `key` 加上 `67`：

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

{% hint style="warning" %}
**DLL 名稱與函式名稱的初始 `key` 差異。** 位於 `name_rva` 的 DLL 名稱自 `pos = name_rva` 開始解密，初始金鑰為 `key = name_rva & 0xFF`。依名稱匯入的項目則指向位於 `hint_name_rva` 的 `IMAGE_IMPORT_BY_NAME` 結構，其 ASCII 符號字串前帶有 2 位元組的 `Hint`：解密起點為 `pos = hint_name_rva + 2`，但初始金鑰仍是 `hint_name_rva & 0xFF`（即整個結構的 RVA，而非 `(hint_name_rva + 2) & 0xFF`）。
{% endhint %}

## 逐頁程式碼擾碼（`dd8`）

可執行程式碼區段可視組建設定額外套用一層稀疏 XOR 擾碼：將每個 4,096 位元組分頁切為 256 個 16 位元組區塊，在區塊 `1..255` 中各挑選 1 個位元組與 `key & 0xFF` 做 XOR（每頁共修改 255 個位置；區塊 `0` 僅推進 `key`，不做 XOR）：

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

{% hint style="info" %}
**擾碼模式的判定方式。** 容器標頭並未記錄 64 位元位移量（`0`、`15` 或不轉換）與 32 位元公式（`page + 1`、`0x8000 * (page + 1)` 或不轉換），且許多原生 DLL 的 `.text` 根本未套用擾碼：
1. **64 位元 CRT 進入點檢查：** 對 `不轉換`、`shift 0` 與 `shift 15` 三種候選模式測試 18 位元組的 MSVC 進入點存根（`48 83 EC ib / E8 rel32 / 48 83 C4 ib / E9 rel32`，且前後堆疊立即值一致）；若僅有單一模式能讓 `call` 與 `jmp` 目標同時落在 `.text` 內，即直接採用該模式。
2. **64 位元 `RET` + `int3` 函式結尾評分：** 若無法由進入點唯一判定，則抽樣 `.text` 內部分頁，統計 `0xC3`（`RET`）後緊接至少 4 個 `0xCC` 填補位元組的總長度；勝出模式必須比未轉換基準多出至少 `8` 位元組。
3. **擾碼位置 `0xCC` 備援判定（64 位元與 32 位元）：** 在 64 位元僅當所有 `RET + int3` 分數皆為零時啟用（32 位元則固定使用此法），統計各擾碼位置經 XOR 還原後變為 `0xCC` 的數量；最高分模式必須至少達未轉換基準的 `2` 倍且命中數不少於 `8`，否則保留 `.text` 原樣不動。
{% endhint %}
