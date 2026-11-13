---
description: "ローリング XOR チェーン、XOR 右ローテート暗号、3 段バイトローテーション暗号。"
icon: rotate
---

# ローリング鍵暗号とローテーション暗号

各ステージのヘッダーやポインターテーブルの復号には、8 ビットおよび 32 ビットの符号なしラップアラウンド演算に基づく 4 種類の軽量なインプレース暗号が使われます。

{% hint style="success" %}
このページのすべての Python 関数は `verification/verify_docs.py` で自動実行し、独立したリファレンステストベクターとバイト単位で一致することを検証しています。
{% endhint %}

## 共通ビット幅ヘルパー

すべての関数は可変の `bytearray` バッファーをインプレースで書き換えます。

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

## ペイロードのローリング XOR チェーン

`header_kdf`（[コンテナと暗号化ヘッダー](../file-structure/container-layout.md)を参照）と `payload_xor_chain` は同じ `i * i` フィードバック構造を共有していますが、こちらでは `- i` ではなく `+ i` を用い、初期シードを `info[0] + ~decrypt_size` とします。

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

`k` の更新には各暗号文 dword `cell` が順番に組み込まれるため、復号は正確な `decrypt_size`（通常は `info[6] - info[3] + 8192`、全ペイロード復号型のコンパクト PE32 ビルドでは `info[5]`）を用いて `i = 0` から開始する必要があります。

## XOR と右ローテートによる dword 暗号（`dd3`）

このプリミティブは `pos` から `{base_addr, length}` を読み取り、各 dword に対して `key` との XOR、`shift` ビットの右ローテート（64 ビットの各ステージでは `19` または `21`）、および dword インデックス `i` の減算を適用します。

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

PE32 ビルドでは、8 通りの右ローテート幅 `[19, 21, 17, 23, 15, 25, 13, 11]` で対象ステージ（`ThirdStage`）を試行復号し、後続のステージテーブル検証を通過した値を採用します（[PE32・DLL・マーカーなしレイアウト](../loading-and-pe-repair/loading/layout-variants.md)を参照）。

## 3 段バイトローテーション暗号（`dd4` と `dd5`）

これら 2 つのバイト暗号はいずれも各バイトを 3 回左ローテートし、その合間に 2 つの鍵バイト（1 バイト処理するごとに `+1` 更新される `b2` と `b`）を XOR します。

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

`byte_rotate2` では位置 `va + i` の復号結果が `d[va + i]` と `(va + i) & 0xFF` のみで決まり、先行バイトからの状態引き継ぎがないため、ディスクリプターテーブルの探索時にバッファーを書き換えず 4 バイト単位で先読み復号できます。

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

連続配置された 16 バイトのローダーディスクリプター配列は、各エントリの配置 RVA を鍵として `byte_rotate2` で暗号化されており、`length` フィールドが `0` のエントリで終端します。
