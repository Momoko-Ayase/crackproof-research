---
description: "3 バイト要素の Huffman 森、16 ビット表、および 4 種のトークンモードの展開"
icon: file-zipper
---

# Huffman / LZ 圧縮

圧縮されたコンテナーブロックは、[Windows 版の Huffman/LZ 形式](https://app.gitbook.com/s/XSPACE_WINDOWS_JA/data-transforms/compression)と同じ 3 バイト単位の Huffman 木エントリおよび 4 モードのトークン符号化を使用します。テーブル内の各ノードは 3 バイト（`u16 value`、`u8 bit_len`）で構成されます。8 ビットのルックアップで開始ルートノードを選択し、短い符号は 16 ビットのプレフィックステーブルで高速に解決します。それより長い符号は、葉ノード（`value & 0x8000 != 0`）に到達するまで入力ビットを 1 ビットずつ読みながら兄弟ペア（`value` と `value + 1`）を辿ります。

## トークンモード

葉ノードの `value` からビット 15 をクリアすると 10 ビットのシンボルが得られます。ビット `8..9` がモードを選択し、ビット `0..7` が `payload` を保持します。16 ビットのアキュムレーター `pending` の初期値は `0` です。

| モード（`sym & 0x300`） | ペイロード（`sym & 0xFF`） | 動作 |
| --- | --- | --- |
| `0x000` | リテラルバイト | `payload` を 1 バイト出力する（このとき `pending` は `0` でなければならない） |
| `0x100` | カウントバイト | `pending > 0xFF` なら不正として棄却し、`pending = (pending << 8) \| payload` に更新する（出力なし） |
| `0x200` | 単位幅（`1`、`2`、または `4`） | `reps = max(pending, 1)` とし、直前に出力済みの `payload` バイト分を `reps` 回繰り返して出力した後（計 `reps * payload` バイト）、`pending = 0` にリセットする |
| `0x300` | 一致長（`length`） | 現在の出力位置より `distance = pending + length` バイト手前から `length` バイトをコピーし、`pending = 0` にリセットする |

<details>
<summary>トークン展開の具体例</summary>

出力バッファーの末尾（`output_pos = 4`）に 4 バイトのリトルエンディアンワード `11 22 33 44` がすでに書き込まれているとします。

1. 葉 `0x8103`（`mode = 0x100`、`payload = 0x03`）: `pending` が `0x0003` になります。出力は 0 バイトです。
2. 葉 `0x8204`（`mode = 0x200`、`payload = 4`）: 単位幅が `4` バイト、`reps = 3` となるため、`11 22 33 44` が 3 回繰り返され（`12` バイト出力、`output_pos = 16`）、`pending` は `0` にリセットされます。
3. 葉 `0x8104`（`mode = 0x100`、`payload = 0x04`）に続いて `0x8306`（`mode = 0x300`、`payload = 6`）: `length = 6`、`distance = 4 + 6 = 10` となり、`output[6..12]` から 6 バイトがコピーされた後、`pending` が `0` にリセットされます。
</details>

## 検証時の不変条件

* **ランレングス充填（`0x200`）:** `payload` は `1`、`2`、`4` のいずれかであり、出力バッファーに少なくとも `payload` バイトがすでに存在し、かつ `output_pos + max(pending, 1) * payload` が `out_len` を超えてはなりません。
* **後方参照コピー（`0x300`）:** `distance = pending + length` は `distance <= output_pos` かつ `output_pos + length <= out_len` を満たす必要があります（`distance < length` で参照元と出力先が重なる場合も、1 バイトずつ順方向にコピーする処理として有効です）。
* **終端の完全一致:** `output_pos == out_len`、`pending == 0`、および `div_ceil(consumed_bits, 8) == src_len` がすべて成り立つ場合にのみ展開成功となります。範囲外のノードインデックス、0 ビット長の葉、`pending` のオーバーフロー、または未消費の末尾バイトがある場合、コンテナーのデコードは失敗します。
