---
description: "KONN シグネチャによる検出、ネイティブ／マネージド PE の分類、レイアウト系統。"
icon: fingerprint
---

# フォーマット判定とビルド系統

## データ内容に基づく判定とモジュール分類

次の 2 条件を満たすファイルは、外側コンテナのシグネチャに一致します。

1. ファイルサイズが `4128` バイト（`0x1020`）以上であり、`e_lfanew`（`u32@0x3C`）が有効な `PE\0\0` シグネチャを指していること。
2. オフセット `4096` に対して `header_kdf` を実行した結果が `info[1] == 0x4E4E4F4B`（`KONN`）になること。

この両方を満たせば保護コンテナの候補と判定できます。完全な検証には、`info` が示す各スライスの範囲チェック、ステージディスクリプターの妥当性確認、およびステージチェックサムまたは試行展開の成功が必要です。

コンテナと判定した後は、標準の PE ヘッダーフィールドから対象を 4 種類のモジュール種別に分類できます。

* `IMAGE_FILE_HEADER.Characteristics & 0x2000`（`IMAGE_FILE_DLL`）で DLL と EXE を区別します。
* データディレクトリ `14`（`IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR`。オプションヘッダー先頭から PE32 では `+96`、PE32+ では `+112` の位置からデータディレクトリ配列が開始）でマネージドアセンブリ（.NET）とネイティブバイナリを区別します。

| `IMAGE_FILE_DLL` | CLR RVA (`DD[14]`) | モジュール種別 |
| --- | --- | --- |
| `0` | `0` | `native-exe` |
| `0` | 非ゼロ | `managed-exe` |
| 非ゼロ | `0` | `native-dll` |
| 非ゼロ | 非ゼロ | `managed-dll` |

マネージド EXE は、ネイティブ EXE と同じ EXE 形式のコンテナを使用します。

```python
MAGIC_KONN = 0x4E4E4F4B  # the shell stamp

def detect(file_data):
    """Return ("native-exe" | "managed-exe" | "native-dll" | "managed-dll",
    magic) for a protected file, or None when the file is not protected by
    this scheme."""
    if len(file_data) < 4128:
        return None
    pe_off = get_u32(file_data, 0x3C)
    if file_data[pe_off:pe_off + 4] != b"PE\0\0":
        return None
    info = header_kdf(file_data)
    if info[1] != MAGIC_KONN:
        return None

    characteristics = get_u16(file_data, pe_off + 4 + 18)   # IMAGE_FILE_HEADER
    is_dll = bool(characteristics & 0x2000)                 # IMAGE_FILE_DLL

    # COM descriptor (CLR) data directory: managed vs native, EXE and DLL alike.
    # Data directories start at optional-header +96 on PE32, +112 on PE32+.
    opt_magic = get_u16(file_data, pe_off + 24)             # 0x10B / 0x20B
    dd_base = 112 if opt_magic == 0x20B else 96
    clr_rva = get_u32(file_data, pe_off + 24 + dd_base + 14 * 8)
    managed = bool(clr_rva)

    if is_dll:
        return ("managed-dll" if managed else "native-dll", info[1])
    return ("managed-exe" if managed else "native-exe", info[1])
```

{% hint style="info" %}
データディレクトリを参照する際は、必ず先にオプションヘッダーのマジック値（`0x10B` または `0x20B`）を確認してください。`DD[14]` の位置は PE32 では `pe + 0xE8`、PE32+ では `pe + 0xF8` です。誤ったオフセットを読むと、32 ビットのネイティブバイナリをマネージドアセンブリと誤判定するおそれがあります。
{% endhint %}

## 確認されているレイアウト軸

保護された Windows ファイルは 4 つの構造軸で分類できます（ただし実在するのは特定の組み合わせに限られ、専用 DLL コンテナは 64 ビットのマーカーあり構成のみ、外部コンパニオン構成は PE32+ の EXE 形式シェルのみです）。

* **ビット幅:** PE32+（`0x20B`、64 ビット）と PE32（`0x10B`、32 ビット）は `header_kdf` と基本暗号プリミティブを共有していますが、設定テーブルの構造、ステージ数、インポートテーブルやヘッダーの再構築規則は異なります（PE32 シェルにはさらに標準型とコンパクト型の派生があります）。
* **モジュール種別:** `native-exe`、`managed-exe`、`native-dll`、`managed-dll` の 4 種類があります。マネージドビルドではディスク上で `COR20` ヘッダーと `BSJB` メタデータルートが平文のまま残っている場合でも、IL メソッド本体は暗号化・圧縮されたセクションペイロード内に格納されています。
* **64 ビット設定データの探索方式:**
  * **マーカーありレイアウト（従来型）:** Stage 5 内にリテラルマーカー `70 6D 00 00 63 6D 00 00`（`"pm\0\0cm\0\0"`）および `00 00 00 40 01 00 00 00`（`0x40000000, 1`）が存在し、そこからの固定相対オフセットでディスクリプター列を辿れます。
  * **マーカーなしレイアウト（新型）:** 上記のマーカーがいずれも省略されており、LFSR スキャン、`trial_byte_rotate2` による範囲判定、`fileCS` との距離スコアリング、および試行展開を組み合わせて Stage 5 の各スロットとバイトコードスタブを特定します。
* **DLL コンテナ形式:**
  * **専用 DLL レイアウト:** 64 ビット DLL 専用コンテナ（`0x20B`）で、設定テーブルが固定オフセット `info[6] + 5592`（`0x15D8`）から始まります。
  * **EXE 形式シェル:** 32 ビットまたは 64 ビット DLL を EXE と同じ多段シェルで包む形式で、オプションとして[外部コンパニオンファイル（`._`）](companion-layout.md)への分割にも対応しています。
