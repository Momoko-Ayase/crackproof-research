---
description: "Unity IL2CPP の -GMD MethodDef トークン難読化と鍵なし構造復元"
icon: table
---

# il2cpp メタデータ難読化

Unity IL2CPP の Windows ビルドでは、CrackProof のオプションである `-GMD` モードを有効にすると、保護対象 PE（`GameAssembly.dll`）と併せて `global-metadata.dat` も改変され、すべての `Il2CppMethodDefinition` エントリの `token` フィールドが書き換えられます。

## 仕組みと未復元時のクラッシュ症状

起動時、IL2CPP は `(token & 0x00FFFFFF) - 1` をインデックスとして `Il2CppCodeGenModule.methodPointers` および `invokerIndices` を参照し、各メソッドのコンパイル済みコードポインタとインボーカを解決します。これらの配列はモジュール内のコンパイル済みメソッド数ちょうどに確保されるため、IL2CPP はモジュールごとの `MethodDef` RID が `1..=methodPointerCount` の連番になっていることを前提としています。

`-GMD` はこの連番 RID を疎な ECMA-335 形式のトークンへと置き換えます（たとえばコンパイル済みメソッド数が約 14,000 個のモジュール内で、RID が約 55,000 に達するような値が格納されます）。保護されたプロセス内では IL2CPP が読み取る前に CrackProof のランタイムがこれらを再マップしますが、`global-metadata.dat` を復元せずに `GameAssembly.dll` だけを静的にアンパックすると、`il2cpp_init` 実行中に `(token_row - 1)` が配列境界外を参照します（典型的には `System.Array` のインターフェースメソッド初期化中に `0xC0000005` でクラッシュします）。

## 鍵不要の構造的復元

`Il2CppMethodDefinition` の各行は宣言元の型（`Il2CppTypeDefinition`）ごとに連続して格納され、型もモジュール（`Il2CppImageDefinition`）ごとに連続して格納されています。そのため、各メソッドの本来の正規トークンはテーブルの並び順だけから一意に決まり、復元に鍵は一切不要です。

```text
local_index = method_index - image_first_method_index
new_token   = 0x06000000 | ((local_index + 1) & 0x00FFFFFF)
```

フィールドトークンと型トークンは元から正規のままであり、変更されません。未難読化の `global-metadata.dat` に対して同じ計算を適用しても `new_token` は既存の `token` と一致するため、この変換はべき等（idempotent）です。

## バージョン 31 のレイアウト定数

| 項目 | 値 |
| --- | --- |
| サニティマジック（`+0x00`） | `0xFAB11BAF` |
| メタデータバージョン（`+0x04`） | `31` |
| ヘッダ内の `{offset, size}` ペア | `methods @0x30`、`types @0xA0`、`images @0xA8` |
| レコードストライド | `method = 0x24`、`type = 0x58`、`image = 0x28` |
| 主要フィールド | `method.token`（`+0x18` の `u32`）、`type.methodStart`（`+0x24` の `u32`）、`type.method_count`（`+0x40` の `u16`）、`image.typeStart`（`+0x08` の `u32`）、`image.typeCount`（`+0x0C` の `u32`） |

復元後のバイト列を書き出す前には、`0xFAB11BAF`、`version == 31`、各テーブルがファイルサイズ内に収まること、サイズが各レコードストライドで割り切れること、および各メソッド範囲が単一イメージに連続して属していることを検証します。なお、Android 版の IL2CPP ビルドではシード付きの 5 ラウンド RID／`methodIndex` 置換が使われており、実行時にモジュール `0x0C` が復元します（バージョン 31 ではフォールバックとして `-GMD` も併用されます）。詳細は Android 編の[メソッドトークン](https://app.gitbook.com/s/XSPACE_ANDROID_JA/metadata/method-tokens)を参照してください。
