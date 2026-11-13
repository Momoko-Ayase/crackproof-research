---
description: "CLI コマンド、検査レポート、フォルダー・APK 処理、表示言語、フラグ、終了コードのリファレンス。"
icon: terminal
---

# 使い方

```text
senbei [inspect|unpack] <file|folder> [--out DIR] [-v|--verbose] [-q|--quiet]...
    [--json] [--dry-run] [--threads N] [--color auto|always|never] [--scan-all]
    [--strict-integrity] [--max-entry-mib N] [--max-total-mib N]
    [--max-entries N] [--max-depth N] [--no-log] [--no-pause]
    [-V|--version] [-h|--help]
```

`senbei <path>` は `senbei unpack <path>` と同等です。`<file|folder>` の前に置かれた `inspect` と `unpack` はサブコマンドとして解釈されます（`inspect` という名前のファイルやフォルダーを対象にする場合は `./inspect` または `.\inspect` と指定してください）。

## 主なワークフロー

{% tabs %}
{% tab title="アンパック" %}
復元されたファイルは、拡張子の直前に `.unpack` を付けた名前で `<parent>/unpack/`（単体ファイル指定時）または `<root>/unpack/`（フォルダー指定時）配下に書き出されます。`--out DIR` を指定すると、出力ファイルと実行ログの保存先をまとめて変更できます。

```cmd
senbei app.exe
senbei app.exe --out C:\out
senbei game.apk --out C:\out
senbei "C:\Games\SampleTitle"
```

`global-metadata.dat` については、メソッドトークンまたはインデックスが実際に変化した場合にのみ `global-metadata.unpack.dat` を書き出します。すでに正規化済みのファイルや未対応バージョンは、フォルダー実行時にはスキップされ、単体ファイルを直接アンパックした際にはエラーとして報告されます。
{% endtab %}

{% tab title="検査と JSON 出力" %}
`inspect` はメモリ上で完全な静的復元を実行して調査用の構造情報を収集します。出力ファイルや実行ログは一切保存せず、ターゲットの実行も行いません。

```cmd
senbei inspect module.dll
senbei inspect module.dll --json
senbei inspect module.dll --strict-integrity --json
```

レポートには、入力ファイルのハッシュ、パース済みの PE/ELF/メタデータヘッダー、復号された保護テーブル、試行したすべての復元ルートと棄却理由、採用されたルート、検出された各ステージのパラメーター（物理ファイルオフセット、コンパニオン連結オフセット、作業イメージ上の RVA を区別して記録）、および静的検証の結果が含まれます。
{% endtab %}

{% tab title="ドライランと CI" %}
`--dry-run` は出力ファイルやログを保存せず（また `inspect` 用のトレースも収集せず）に復元と静的検証のみを実行します。Android 展開用の一時作業ディレクトリは自動的に削除されます。

```cmd
senbei unpack module.dll --dry-run
senbei unpack module.dll --dry-run --json --strict-integrity
senbei unpack folder --strict-integrity --no-pause -q
```

`inspect` と `--dry-run` はどちらも `--out` と併用できません。
{% endtab %}
{% endtabs %}

## Android ライブラリとパッケージ

Senbei は保護された AArch64 `.so` バイナリを復元し（`libil2cpp.unpack.so` または `<stem>.unpack.so`）、`.apk`・`.apks`・`.xapk` パッケージも直接処理します。

1. まず ZIP のセントラルディレクトリを読み取り、`.apks`/`.xapk` バンドル内のネストされた `.apk` エントリを `--max-depth` の深さまでたどります。
2. 設定された `--max-entry-mib`、`--max-total-mib`、`--max-entries` のバジェット内で、`.so` およびファイル名が完全一致する `global-metadata.dat` エントリのみを一時ファイルへストリーム展開します。
3. 外部の `v24.1` メタデータを同一アプリのモジュール `0x0C` とペアリングし（split APK 間では `AndroidManifest.xml` のパッケージ名＋バージョン、展開済みディレクトリでは `<root>/lib/<abi>/` ＋ `<root>/assets/` でスコープ判定）、埋め込みスリム形式の `v24` XOR データは `global-metadata.unpack.dat` へ書き出します。同一内容の単体ファイルとパッケージ内ファイルの重複も自動的に除外されます。

## フォルダー走査とコンパニオンファイル

フォルダーモードではサブディレクトリを再帰的に走査します。その際、`unpack` ディレクトリ（大文字・小文字を区別せず判定。ただし走査ルート自体が `unpack` の場合は除く）と、ルート配下の NTFS リパースポイントはスキップされます。

* **走査対象のファイル名（大文字・小文字を区別しない）:** `.exe`、`.dll`、`.so`、`global-metadata.dat`、`.apk`、`.apks`、`.xapk`。マニフェストのパッケージ名とバージョンが一致する同一フォルダー内の split `.apk` 群は自動でグループ化されます。`4,128` バイト未満の候補は、`--scan-all`（または `SENBEI_SCAN_ALL`）が指定されていない限りファイルを開かずにスキップされます。
* **Windows の `._` コンパニオンファイル:** 同じフォルダーにある `.exe._` および `.dll._` ファイルは対応するスタブから読み込まれ、スキップ件数には計上されません。コンパニオン形式のマネージド DLL では、復号された IL メソッド本体にスタブ側の `COR20` テーブルを重ね合わせるため、`Module.dll` と `Module.dll._` の両方が必要です。

{% hint style="info" %}
**コンパニオン関連の診断メッセージ:** `Missing companion file` は、PE32+ のエントリレコードに `._` コンパニオン宣言（`~0x1000` および `~"._\0\0"`）が明示されており、かつ `<input>._` が存在しない場合にのみ報告されます。`Companion doesn't match` は、`<input>._` が 32 バイト未満であるか、先頭 `0x00..0x20` のヘッダーが `stub[0x1000..0x1020]` と一致しないことを示します。
{% endhint %}

## 表示言語と端末カラー

Senbei は `en`（英語）、`zh-CN`（簡体字中国語）、`zh-TW`（繁体字中国語）、`ja`（日本語）、`ko`（韓国語）の5つの表示言語に対応しています。

{% tabs %}
{% tab title="Command Prompt" %}
```cmd
set SENBEI_LANG=ja
senbei inspect module.dll
```
{% endtab %}

{% tab title="PowerShell" %}
```powershell
$env:SENBEI_LANG = "zh-TW"
senbei inspect module.dll
```
{% endtab %}

{% tab title="POSIX / Bash" %}
```sh
SENBEI_LANG=ko senbei inspect module.dll
```
{% endtab %}
{% endtabs %}

* **ロケール解決:** `SENBEI_LANG` の値は `.encoding` や `@modifier` サフィックスを除いたうえで、`-` と `_` のどちらでも大文字・小文字を区別せずに照合されます。文字体系サブタグ（`Hans` / `Hant`）は地域サブタグより優先されます（`zh-Hans-HK` -> 簡体字中国語、`zh-Hant` / `zh-TW` / `zh-HK` / `zh-MO` -> 繁体字中国語）。`SENBEI_LANG` が未設定の場合は Windows の UI 言語リストまたは `LC_ALL` / `LC_MESSAGES` / `LANG` / `LANGUAGE` を順に確認し、該当がなければ英語にフォールバックします。
* **英語のまま維持される出力:** `--json` 出力、保存される `.log` ファイル、`inspect` の構造テーブル、`-v` のステージ詳細行は常に英語で出力されます。ローカライズされたエラー表示に加えて詳細な内部エラー情報がある場合は、次の行に英語の詳細メッセージが出力されます。
* **カラー出力（`--color MODE` または `--color=MODE`）:** `auto`（既定値）はストリームごとに TTY 判定を行い、`NO_COLOR` が非空の場合や `TERM=dumb` の場合はカラーを無効化します。`always` は通常のテキスト出力で ANSI カラーを強制し、`never` は無効化します。`--json` および `.log` ファイルに ANSI エスケープシーケンスが含まれることはありません。

## 静的検証とブラウザー版の上限

静的検証では、復元後の PE ヘッダー、セクションマッピング、エントリポイント到達性と CRT 分岐先、最大 256 個のインポート記述子、ネイティブデータディレクトリ、CLR `BSJB` ストリームのほか、Android ELF の `PT_LOAD` 境界、動的テーブル、シンボルハッシュ、再配置、コンストラクターポインターを検査します。構造上の警告や致命的でない不整合がある出力も `unpack` 時にはファイルとして書き出され、`suspect` として計上されます。`--strict-integrity` を指定すると、`unpack`・`--dry-run`・`inspect` のいずれにおいても `suspect` が1件以上検出された時点で終了コードが `1` になります。

WebAssembly ブラウザー版では、**Input limit per module (MiB)** の既定値は `256`（`8`..`4096` MiB、メモリへ読み込む前にスタブと `._` コンパニオンの合計サイズで判定）であり、**Export JSON** から `senbei.browser-report` v1 ファイルをダウンロードできます。Android の `.so` およびパッケージの復元にはネイティブ版の `senbei` または `senbei-gui` を使用してください。

## フラグ一覧

| フラグ | 動作 |
| --- | --- |
| `--out DIR` | アンパック結果と実行ログを `DIR` 配下に書き出します（`unpack` モード専用）。 |
| `--dry-run` | 出力ファイルやログを保存せずに復元と静的検証を実行します。 |
| `--json` | バージョン付き JSON レポートを `stdout` に出力します（`-q -q` 指定時も有効）。実行ログ保存と終了時の一時停止は無効化されます。 |
| `--threads N` | ワーカースレッド数の上限（`N >= 1`）。`SENBEI_THREADS` より優先され、`1` で逐次実行になります。 |
| `--color auto\|always\|never` | 端末の ANSI カラー出力を制御します（`--color=MODE` 形式も可）。 |
| `-v`, `--verbose` | ステージごとの進捗行を表示します。 |
| `-q`, `--quiet` | バナーとファイル単位の進捗を非表示にします。`-q -q`（個別フラグとして2回指定）ですべての `stdout` と実行時の `stderr` を抑制します。 |
| `--no-log` | `senbei-YYYYMMDD-HHMMSS.log` の書き出しを省略します。 |
| `--scan-all` | フォルダー走査時に `4,128` バイト未満の対象拡張子ファイルもプローブします。 |
| `--strict-integrity` | 復元されたイメージに `suspect` 判定が1件でもあれば終了コード `1` を返します（`unpack`、`--dry-run`、`inspect` に適用）。 |
| `--max-entry-mib N` | Android の単一 ZIP エントリ、復号コンテナー、アーティファクト、または出力ファイルあたりの最大サイズ（MiB、`N >= 1`、既定値 `2048`）。 |
| `--max-total-mib N` | Android アーカイブ展開およびタスク単位の復元における累積データ量の上限（MiB、`N >= 1`、既定値 `8192`。プロセスのピーク RAM 上限ではありません）。 |
| `--max-entries N` | ネストされた Android アーカイブ全体でのアーカイブエントリ数および Stage 2 レコード数の上限（`N >= 1`、既定値 `100000`）。 |
| `--max-depth N` | ネストされた Android APK および Stage 2 ストリームの最大ネスト深さ（`0` 指定可、既定値 `32`）。 |
| `--no-pause` | Windows エクスプローラーから起動した際の終了時プロンプトを省略します。 |
| `-V`, `--version` / `-h`, `--help` | バージョン情報またはヘルプを表示して終了コード `0` で終了します。 |

## 終了コード

| コード | 意味 |
| --- | --- |
| `0` | コマンドが正常完了しました（`unpack`、`--dry-run`、`inspect`、`--help`、または `--version` でターゲットエラーがなく、`--strict-integrity` 指定時は `suspect` もない状態）。 |
| `1` | 1件以上のターゲットで処理に失敗した、走査・プローブ対象を読み取れなかった、Android のリソース上限を超過した、または `--strict-integrity` 指定時に `suspect` イメージが検出されました。 |
| `2` | コマンドライン引数が不正です（引数なしでの `senbei` 実行、併用不可フラグの組み合わせ、無効な数値上限など）。 |
