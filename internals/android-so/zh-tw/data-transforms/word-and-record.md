---
description: "GF(2^32) 字組乘法、串流標頭與記錄描述元加解密，以及 0x9D 受保護描述元。"
icon: rotate
---

# 字組、串流與記錄加解密

Android 串流不再沿用 Windows 版本的滾動 XOR 運算，而是改以 GF(2³²) 有限體乘法搭配 32 位元模數算術，保護串流標頭、`0x5C` 位元組記錄描述元及 `0x9D` 受保護描述元。

## GF(2³²) 固定常數乘法

`gf32_mul_fixed(value)` 會先取輸入的低 32 位元，再於約化多項式 `0x579357EB` 定義的 GF(2³²) 上乘以固定常數 `0x94511DD2`：

```text
MASK32 = 0xFFFFFFFF

def gf32_mul_fixed(value):
    value &= MASK32
    multiplier = 0x94511DD2
    result = 0
    while multiplier:
        if multiplier & 1:
            result ^= value
        carry = value >> 31
        value = (value << 1) & MASK32
        if carry:
            value ^= 0x579357EB
        multiplier >>= 1
    return result
```

在串流標頭、記錄描述元與[容器標頭](container.md)的各項公式中，`gf(x)` 皆代表 `gf32_mul_fixed(x)`。

## Stage 1 字組加解密

32 位元組的 Stage 1 參數標頭與加密的 Stage 2 映像皆使用無號 32 位元溢位迴繞運算；對字組索引 `i` 與建置家族常數 `C`（`0xBF20165D` 或 `0xBF189BDD`）：

```text
plain[i] = ((cipher[i] + (i + 3) * key) ^ (C * (i + 1))) & MASK32
```

在 32 位元組參數標頭中，第 `0` 個字組提供 `key = cipher[0] ^ C`，等第 `1..7` 個字組解碼完成後再寫回 `plain[0] = key`。標頭欄位的結構驗證條件請參閱 [Stage 1 標頭](../file-format/stage1.md)。

## 串流標頭加解密

每條直譯器串流（根層級為 `0xE2`，巢狀層級為 `0xE3`..`0xE8`）開頭皆為兩個小端序 dword（`cipher0`、`cipher1`）。目前已觀測到兩個常數家族；兩者皆取中間乘積與總和的低 32 位元，算出 `dw0`（記錄筆數）與 `G`（該串流的描述元種子）：

{% tabs %}
{% tab title="家族 A" %}
```text
K   = (sid * 0x9D323CD7) & MASK32
K   = ((K << (sid & 0xB)) + (K >> (sid & 7))) & MASK32
dw0 = (gf((cipher0 + 0xCBF0C1D8) & MASK32) ^ ((K + 0x4178CB33) & MASK32)) & MASK32
dw1 = (gf((cipher0 + cipher1) & MASK32)    ^ ((K + 0xF119421B) & MASK32)) & MASK32
G   = (K + 0x5590AD79 + dw1) & MASK32
```
{% endtab %}

{% tab title="家族 B" %}
```text
K   = (sid * 0x9D323CD7) & MASK32
mix = ((K >> (sid & 7)) + 0x5E727D74) & MASK32
mix = (mix + ((K << (sid & 0xB)) & MASK32) + 0xF71E3005) & MASK32
dw0 = (gf((cipher0 + 0xCBF0C1D8) & MASK32) ^ ((0xEBE81DBA + mix) & MASK32)) & MASK32
dw1 = (gf((cipher1 + cipher0) & MASK32)    ^ ((0xEBE81DBA * 5 + mix) & MASK32)) & MASK32
G   = (dw1 + mix) & MASK32
```
{% endtab %}
{% endtabs %}

實務解析時會依序嘗試兩個家族，並以 [Stage 2 串流](../file-format/stage2-streams.md)中的描述元結構條件判定哪一組成立。

## 記錄描述元加解密

每筆 `0x5C` 位元組記錄描述元由 23 個小端序 dword 組成。給定串流種子 `G` 與從 `0` 起算的記錄索引 `idx`，兩個常數家族皆共用同一套解密迴圈：

```text
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

{% hint style="warning" %}
`off` 每輪遞增 4 位元組，因此 `(off + 3) & 5` 會在 `1`（偶數字組：`(0 + 3) & 5 = 1`）與 `5`（奇數字組：`(4 + 3) & 5 = 5`）之間交替。此外，`feedback` 是以原始密文字組 `cipher` 更新，而非解密後的 `value`。
{% endhint %}

## `0x9D` 受保護描述元

直接模組 `0x9D` 開頭是一筆 `0x5C` 位元組的 `ProtectedDescriptor`，使用[模組 `0x9B`](module-config.md) 提供的 `header_seed` 加密：

```text
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

合法明文必須滿足 `words[0] == 0x9D`（`command_id`）、`words[2] == 0x5C`（`outer_offset`，緊接於描述元之後），以及 `words[6..23] == 0`。其中 `words[2..5]` 分別給出主要 ELF 映像容器的 `(outer_offset, outer_size)`，以及[容器轉換](container.md)中輔助重定位／符號容器的 `(aux_offset, aux_size)`。
