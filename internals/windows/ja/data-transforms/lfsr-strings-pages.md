---
description: "0x8003 LFSR スタブ暗号、RVA 鍵のインポート名暗号、ページ単位コードスクランブル。"
icon: wave-square
---

# LFSR・文字列・ページ変換

## LFSR キーストリーム（`dd6`） <a href="#lfsr-keystream-dd6" id="lfsr-keystream-dd6"></a>

96 バイト固定長の[ビルド固有バイトコードスタブ](bytecode-transform.md)の各スロットでは、`pos + 95` に未暗号化のプログラム長（`<= 95`）が格納されており、`d[pos .. pos + length]` が固定シードのガロア LFSR（初期状態 `1`、生成多項式 `0x8003`、1 バイトあたり LSB ファーストで 8 ビット出力）でマスクされています。

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

キーストリームはスロットの配置アドレスによらず先頭からのバイト位置のみで決まるため、あらかじめ計算した 95 バイトのキーストリームテーブルを使えば、任意のオフセットにある 96 バイト候補ウィンドウを高速に検査できます。

## インポート名文字列暗号（`dd7`）

暗号化された DLL 名およびインポートシンボル名には、NUL 終端のローリングバイト暗号が使われます。各バイトの上位・下位ニブルを入れ替え（`ror8(..., 4)`）、`key` を減算します。暗号文の途中に `0x00` が生じないようエンコード時に退避された値（平文が `(-key) & 0xFF` のケース）を復元するため、減算結果が `0` の場合は `(-key) & 0xFF` に置き換え、その後 `key` に `67` を加算します。

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
**DLL 名と関数名における初期 `key` の違い。** `name_rva` にある DLL 名は `pos = name_rva`、初期鍵 `key = name_rva & 0xFF` で復号を開始します。一方、名前指定インポートが指す `hint_name_rva` の `IMAGE_IMPORT_BY_NAME` レコードでは、ASCII シンボル文字列の先頭に 2 バイトの `Hint` フィールドが付いているため、復号開始位置は `pos = hint_name_rva + 2` になりますが、初期鍵には `(hint_name_rva + 2) & 0xFF` ではなくレコード先頭 RVA に基づく `hint_name_rva & 0xFF` をそのまま使用します。
{% endhint %}

## ページ単位のコードスクランブル（`dd8`）

ビルドによっては、実行可能コードセクションにページ単位の間引き XOR スクランブルが追加されます。4,096 バイトの 1 ページ（16 バイト × 256 ブロック）のうち、先頭のブロック `0` では XOR を行わず `key` の更新のみを行い、続くブロック `1..255` の各 16 バイトブロックにつき 1 バイト（計 255 バイト）を `key & 0xFF` と XOR して書き換えます。

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
**スクランブルモードの判定方法。** 64 ビット版のシフト量（`0`、`15`、または未適用）も 32 ビット版の計算式（`page + 1`、`0x8000 * (page + 1)`、または未適用）もコンテナヘッダーには記録されておらず、多くのネイティブ DLL では `.text` にスクランブル自体がかかっていません。そのため、以下の手順でモードを判定します。
1. **64 ビット CRT エントリ判定:** `unchanged`（未変換）、`shift 0`、`shift 15` の 3 通りについて 18 バイトの MSVC エントリスタブ（スタック即値が一致する `48 83 EC ib / E8 rel32 / 48 83 C4 ib / E9 rel32`）を検査し、`call` と `jmp` の両ターゲットが `.text` セクション内に収まる唯一の候補があれば即座に採用します。
2. **64 ビット `RET` + `int3` エピローグスコア:** 上記で決まらない場合、`.text` 内部のページをサンプリングし、`0xC3`（`RET`）に 4 バイト以上の `0xCC` パディングが続く列の合計バイト長をスコア化します。未変換のベースラインより `8` バイト以上増加した候補を採用します。
3. **変化バイトの `0xCC` フォールバック（64 ビットおよび 32 ビット）:** 64 ビットですべての `RET + int3` スコアが `0` だった場合のみ（32 ビットでは常にこの方式を使用）、書き換えによって `0xCC` になった箇所の個数を数え、未変換ベースラインの `2` 倍以上かつ `8` 個以上に達した候補を採用します。条件を満たす候補がなければ `.text` を未変換のまま維持します。
{% endhint %}
