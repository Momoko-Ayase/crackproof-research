---
description: "/FIXEDとASLRの再配置規則、系統別の.text変換順序、CLRメタデータの部分復元。"
icon: cubes
---

# ベース再配置・ページ変換・CLR データ

## ベース再配置と `/FIXED`・ASLR ポリシー

* **単一ファイルの 64 ビット・マーカーあり EXE および 32 ビット EXE（`/FIXED`）：** パッカーがベース再配置を破棄し `DllCharacteristics` をクリアしています。静的再構築でも `DataDirectory[5]` と `DllCharacteristics` をゼロクリアし、EXE が既定の `ImageBase` にロードされるようにします。
* **すべての DLL（32 ビット・64 ビット、全系統）：** DLL は再配置可能でなければならないため、`DataDirectory[5]` を維持し、`IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE`（`0x0040`）を確実に立てたうえで、PE32 DLL では無効化されていた TLS のベース再配置を再有効化します。
* **マーカーなし 64 ビットおよび外部コンパニオンファイル（`._`）ビルド：** 有効な ASLR フラグ（`DYNAMIC_BASE` / `HIGH_ENTROPY_VA`）と `DataDirectory[5]` を維持します（コンパニオンファイルから TLS を復元した場合は 4 個の `DIR64` TLS 再配置エントリを追記します）。

## `.text` ページスクランブル（`dd8`）の実行順序

マーカーなしビルドでは暗号化されたインポート文字列と平文の CLR メタデータが `.text` 内部に格納されているため、マーカーありパイプラインとマーカーなしパイプラインでは `dd8` を実行するタイミングを変える必要があります。

```mermaid
flowchart TB
    subgraph Marker["64ビット・マーカーありパイプライン"]
        direction LR
        M1["セクション復元"] --> M2["walk5 インポート復号"] --> M3["セクションヘッダー・エクスポート"] --> M4[".text dd8"] --> M5["EP・データディレクトリ復元"] --> M6["CLR・TLS 復元"]
    end
    subgraph Markerless["64ビット・マーカーなしパイプライン"]
        direction LR
        L1["セクション復元"] --> L2["セクションヘッダー・エクスポート"] --> L3["EP・データディレクトリ復元"] --> L4[".text dd8\n(EP が .text 内の場合のみ)"] --> L5["DD[1] IDT インポート復号"] --> L6["CLR・TLS 復元"]
    end
```

マーカーなしビルドでは、セクションヘッダーおよび EP / データディレクトリの復元後（`AddressOfEntryPoint` が `.text` 内に収まる場合のみ実行）、かつ `DD[1]` の IDT インポート名復号や CLR メタデータの上書きコピーより**前に** `dd8` を実行します。これにより、復号直後のインポート文字列が `dd8` で再びスクランブルされたり、上書きコピーした `COR20` / `BSJB` のバイト列が破壊されたりするのを防ぎます。

## CLR メタデータのピンポイント復元

マネージドアセンブリの CrackProof ビルドでは、IL メソッド本体がセクションペイロード内で暗号化される一方、ECMA-335 メタデータ構造体は外側ファイルまたはコンパニオンスタブ内に平文で保持されています。

* **単一ファイルのマーカーなし 64 ビット：** `dd8` の実行後に、`COR20` ヘッダー（`cb == 0x48`）と `BSJB` メタデータストリームをそれぞれの RVA に上書きコピーします。
* **単一ファイルのマーカーあり 64 ビット：** `COR20`、`BSJB` メタデータ、および `COR20.Resources`（`+0x18`）を上書きコピーします。
* **マネージドのコンパニオンファイル（`._`）DLL：** スタブ PE から `COR20`（`0x48` バイト）を上書きコピーするとともに、参照先の 7 つのサブ領域のうち非ゼロのものをすべてコピーします（必須の `MetaData`（`BSJB`）に加え、`Resources`、`StrongNameSignature`、`CodeManagerTable`、`VTableFixups`（および参照される各スロット配列）、`ExportAddressTableJumps`、`ManagedNativeHeader`）。

{% hint style="warning" %}
**セクション復元後に CLR を含むセクション全体を丸ごとコピーしてはなりません。** IL メソッド本体は `COR20` や `BSJB` と同じ `.text` セクションに同居しており、`walk4` と `dd8` で復号されています。保護済みファイルやスタブからセクション全体を上書きすると、復号済みのメソッド本体が暗号文で潰れてしまいます（例外として、旧世代の専用 64 ビット DLL パイプラインのみ、`walk4` がメソッド本体を書き込む**前に** CLR セクションを事前コピーします）。
{% endhint %}

`DataDirectory[14]`（PE32 では `pe + 0xE8`、PE32+ では `pe + 0xF8`）が有効な退避コピーのないゼロクリア済み `COR20` ヘッダー（`cb == 0`）を指している場合、`DataDirectory[14]` はクリアされます。なお、Unity IL2CPP タイトルでは CLR ヘッダーを持たないネイティブ DLL として `GameAssembly.dll` がパックされ、`global-metadata.dat` には別途難読化が施されます。詳細は [il2cpp メタデータの難読化](../../analysis/il2cpp-metadata.md)を参照してください。
