---
description: "マジック値、コンテナ計算式、暗号式、PE32/PE32+ オフセット、AL バイトコード一覧"
icon: sliders
---

# 定数・オフセット一覧

## コンテナ定数とマジック値

| 項目 | 値 |
| --- | --- |
| フォーマットマジック（`info[1]`） | `0x4E4E4F4B`（リトルエンディアン ASCII で `KONN`） |
| 外側 PE ヘッダ領域サイズ / `info` オフセット | `4096`（`0x1000`） |
| 暗号化された `info` ヘッダ長 | `32` バイト（`8` DWORD） |
| 検査対象ファイルの最小サイズ | `4128`（`0x1020`）バイト |
| `decrypt_size`（標準 / フルペイロード PE32） | `info[6] - info[3] + 8192` / `info[5]`（コンパクト PE32 のフォールバック） |
| セクションデータのファイルベースオフセット | `(~u32@0x1080 + 0x1000) & 0xFFFFFFFF` |
| コンパニオンファイル（`._`）のペア照合 | `stub[4096..4128] == companion[0..32]` |
| コンパニオン用エントリサンクマーカー（`+53` / `+58`） | `~0x1000` / `~u32("._\0\0")`（単一ファイル PE32+ では `~0`） |
| ペイロードコピー後に `image[info[3]]` へ書き込まれる DWORD | `4096`（`0x1000`） |
| PE32 `EighthStage` クラスタスタンプ | `0x00007679`（存在する場合） |
| 64 ビット Stage 5 マーカー（従来レイアウト） | `70 6D 00 00 63 6D 00 00`（`"pm\0\0cm\0\0"`）および `00 00 00 40 01 00 00 00` |

## 暗号プリミティブとチェックサム早見表

| プリミティブ | 計算式（符号なし 8/32 ビットラップアラウンド） |
| --- | --- |
| `header_kdf` | `info[i + 1] = k ^ cell; k = (i * i) ^ ((k + cell - i) & MASK32)` |
| `payload_xor_chain` | `k0 = info[0] + ~decrypt_size; out = k ^ cell; k = (i * i) ^ ((k + cell + i) & MASK32)` |
| `xor_ror_dwords`（`dd3`） | `v = x ^ key; key += i; out = ror32(v, shift) - i`（64 ビット：`19`/`21`、32 ビット：8 種のシフト値セット） |
| `byte_rotate3`（`dd4`） | `b = ((addr >> 8) + addr) & 0xFF; b2 = b + 1`、`rol8(..., 3)` を 3 回適用し、`b2` 次いで `b` と XOR |
| `byte_rotate2`（`dd5`） | `b = va & 0xFF; b2 = b + 1`、`rol8(..., 2)` を 3 回適用し、`b2` 次いで `b` と XOR（各バイト位置で独立） |
| `lfsr_keystream`（`dd6`） | シード `1`、生成多項式 `0x8003`、LSB ファーストで 8 ビット／バイト。`pos + 95` に平文長 |
| `string_cipher`（`dd7`） | `ror8(b, 4) - key`（`0 -> -key`）、`key += 67`。初期鍵は `name_rva & 0xFF` または `hint_name_rva & 0xFF` |
| `page_scramble`（`dd8`、64 ビット） | `i >= 1` に対し `mixed = ror32(key, 15) + i; key = mixed + i`、`page[i * 16 + (mixed & 0xF)] ^= key & 0xFF` |
| `page_scramble_pe32`（`dd8`、32 ビット） | 事前ステップ `key = ror32(pk, 15)`（`pk = page + 1` または `0x8000 * (page + 1)`）の後、`i = 1..255` を実行 |
| `crc32`・`calculate_checksum` | ビット反転 CRC-32（`0xEDB88320`）。領域チェックサムは `crc32(region) ^ length` |
| `advance_key` | `m in 0..iterations` について `1 .. ((m + 1) * 100)` の総和を加算 |
| `aes_decrypt` | ゼロ IV の AES-CBC、`key_offset + 2` の `u16` ラウンド数、ビッグエンディアン状態ワード、標準 GF(2⁸) 逆 T-table |

## PE ヘッダオフセット（`pe = u32@0x3C`）

| フィールド | PE32+（`0x20B`） | PE32（`0x10B`） |
| --- | --- | --- |
| `Characteristics`（`IMAGE_FILE_DLL = 0x2000`） | `pe + 0x16` | `pe + 0x16` |
| `OptionalHeader.Magic` | `pe + 0x18` | `pe + 0x18` |
| `AddressOfEntryPoint` | `pe + 0x28` | `pe + 0x28` |
| `SizeOfImage` | `pe + 0x50` | `pe + 0x50` |
| `DllCharacteristics` | `pe + 0x5E` | `pe + 0x5E` |
| データディレクトリ配列先頭 | `pe + 0x88`（`136`） | `pe + 0x78`（`120`） |
| Export ディレクトリ（`DD[0]`） | `pe + 0x88` | `pe + 0x78` |
| Import ディレクトリ（`DD[1]`） | `pe + 0x90` | `pe + 0x80` |
| Resource ディレクトリ（`DD[2]`） | `pe + 0x98` | `pe + 0x88` |
| Base Relocation（`DD[5]`） | `pe + 0xB0` | `pe + 0xA0` |
| TLS ディレクトリ（`DD[9]`） | `pe + 0xD0` | `pe + 0xC0` |
| IAT（`DD[12]`） | `pe + 0xE8` | `pe + 0xD8` |
| CLR / COM 記述子（`DD[14]`） | `pe + 0xF8` | `pe + 0xE8` |

## ビルド固有 `AL` バイトコードのオペコード

| バイト列 | 命令 | デコード後の操作 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | スキップ |
| `C0 C0 ib` | `ROL AL, imm8` | `("rol", imm)` |
| `C0 C8 ib` | `ROR AL, imm8` | `("ror", imm)` |
| `FE C0` | `INC AL` | `("inc",)` |
| `FE C8` | `DEC AL` | `("dec",)` |
| `C3` | `RET` | スタブ終端 |

## 検証スイート

上記の各変換は、[検証・リファレンス](https://app.gitbook.com/s/XSPACE_REFERENCE_JA/)に収録されている 25 件の名前付きリファレンスレコードに対する 31 項目の比較を通じて、独立した Rust 実装と照合・検証されています。リポジトリルートで `python verification/run_tests.py` および `python verification/verify_docs.py` を実行すると、すべてのリファレンス実装とドキュメント内コードブロックを再検証できます。
