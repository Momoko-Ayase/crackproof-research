---
description: "GF(2^32) 固定乗算、ストリームヘッダー・レコード記述子暗号、および 0x9D 保護記述子"
icon: rotate
---

# ワード・ストリーム・レコード暗号

Android 版のストリームでは、Windows 版のローリング XOR プリミティブに代わり、ストリームヘッダー、`0x5C` バイトのレコード記述子、および `0x9D` 保護記述子の各層で GF(2³²) 乗算と符号なし 32 ビットのラップアラウンド演算（mod 2³²）が用いられます。

## GF(2³²) 固定乗算

`gf32_mul_fixed(value)` は入力を 32 ビットにマスクし、法多項式 `0x579357EB` のもとで `0x94511DD2` との GF(2³²) 乗算を行います。

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

以降のストリームヘッダー、レコード記述子、および[コンテナーヘッダー](container.md)の各式では、`gf32_mul_fixed(x)` を `gf(x)` と表記します。

## Stage 1 ワード暗号

32 バイトの Stage 1 パラメーターヘッダーと暗号化された Stage 2 イメージはどちらも、ワードインデックス `i` とビルド系統定数 `C`（`0xBF20165D` または `0xBF189BDD`）を使った符号なし 32 ビットのラップアラウンド演算で復号します。

```text
plain[i] = ((cipher[i] + (i + 3) * key) ^ (C * (i + 1))) & MASK32
```

32 バイトのパラメーターヘッダーでは、ワード `0` から `key = cipher[0] ^ C` を算出し、ワード `1..7` の復号後に `plain[0] = key` として書き戻します。各ヘッダーフィールドの不変条件は [Stage 1 ヘッダー](../file-format/stage1.md)を参照してください。

## ストリームヘッダー暗号

すべてのインタープリターストリーム（ルートが `0xE2`、入れ子階層が `0xE3`..`0xE8`）は、リトルエンディアンの 32 ビットワード 2 個（`cipher0`、`cipher1`）から始まります。定数の異なる 2 つのビルド系統が確認されており、いずれも途中の積と和を 32 ビットにマスクしながら `dw0`（レコード数）と `G`（ストリームの記述子シード）を導出します。

{% tabs %}
{% tab title="系統 A" %}
```text
K   = (sid * 0x9D323CD7) & MASK32
K   = ((K << (sid & 0xB)) + (K >> (sid & 7))) & MASK32
dw0 = (gf((cipher0 + 0xCBF0C1D8) & MASK32) ^ ((K + 0x4178CB33) & MASK32)) & MASK32
dw1 = (gf((cipher0 + cipher1) & MASK32)    ^ ((K + 0xF119421B) & MASK32)) & MASK32
G   = (K + 0x5590AD79 + dw1) & MASK32
```
{% endtab %}

{% tab title="系統 B" %}
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

復号時は両方の系統を順番に試行し、[Stage 2 ストリーム](../file-format/stage2-streams.md)で定義されたレコード記述子の構造条件を満たす方を採用します。

## レコード記述子暗号

`0x5C` バイトの各レコード記述子は、リトルエンディアンの 32 ビットワード 23 個で構成されます。両系統とも、ストリームシード `G` と 0 始まりのレコードインデックス `idx` を用いて同一のループで復号します。

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
`off` は反復ごとに 4 バイトずつ進むため、`(off + 3) & 5` の値は `1`（偶数ワード: `(0 + 3) & 5 = 1`）と `5`（奇数ワード: `(4 + 3) & 5 = 5`）を交互に取ります。また、`feedback` は復号後の `value` ではなく、生の暗号文ワード `cipher` で更新されます。
{% endhint %}

## `0x9D` 保護記述子

直接レコードとして格納されるモジュール `0x9D` の先頭には、[モジュール `0x9B`](module-config.md) の `header_seed` で暗号化された `0x5C` バイトの `ProtectedDescriptor` が置かれています。

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

復号後のワード列は、`words[0] == 0x9D`（`command_id`）、`words[2] == 0x5C`（記述子直後を指す `outer_offset`）、および `words[6..23] == 0` をすべて満たす必要があります。ワード `2..5` には、主 ELF イメージコンテナーの範囲 `(outer_offset, outer_size)` と、[コンテナー変換](container.md)で解説する再配置・シンボル用の補助 ELF コンテナーの範囲 `(aux_offset, aux_size)` が格納されています。
