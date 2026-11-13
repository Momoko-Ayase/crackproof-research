---
description: "ネイティブ・マネージドツールのビルド、Senbei 1.3.1 オラクル検証、リリース作成手順。"
icon: hammer
---

# 開発

## ビルド手順

前提環境は Rust `1.98.1` 以降、MASM（`ml` / `ml64`）を含む Visual Studio C++ x86/x64 ビルドツール、および Windows 10/11 SDK です（MSVC `14.51` と SDK `10.0.26100` で検証済み）。マネージド保護と WPF GUI のビルドには、さらに .NET 10 SDK と .NET Framework 4 リファレンスアセンブリが必要です。

{% stepper %}
{% step %}
### ネイティブ CLI と組み込みローダーのビルド

`cargo build` を実行すると、x86 と x64 の両方の C/ASM ランタイムローダーがソースからコンパイルされます。

```powershell
rustup target add i686-pc-windows-msvc
cargo build --release -p arare-cli
```
{% endstep %}

{% step %}
### マネージドメタデータツールのビルド（CLR 入力に必須）

`tools/managed/build.ps1` は NuGet 依存を一切持たず（`dotnet.exe` が既定パスにない場合は `-Dotnet <path>` を指定）、`Arare.ManagedHost.dll`、`Arare.ManagedHost.runtimeconfig.json`、`Arare.Bootstrap.dll` を出力します。

```powershell
& tools/managed/build.ps1
$env:ARARE_MANAGED_TOOLS = (Resolve-Path target/managed-tools).Path
```

`runtime/` または `tools/managed/` 配下のファイルを変更した際は、必ず `tools/managed/build.ps1` を再実行してください。実行時、`arare` および Python テストハーネスは `ARARE_DOTNET` で絶対パスが指定されていない限り `C:/Program Files/dotnet/dotnet.exe` を参照します。
{% endstep %}

{% step %}
### リリースアーカイブのパッケージ作成（任意）

スタンドアロン配布用の `arare-windows-x64` または `arare-windows-x86` アーカイブ（`managed/` を同梱し、任意で `Arare.Gui.exe` も追加可能）を作成します。

```powershell
& tools/package.ps1 -Architecture x64 -IncludeGui
```
{% endstep %}
{% endstepper %}

## テスト

{% tabs %}
{% tab title="ワークスペース検証" %}
標準のワークスペーステストは自動生成されるテスト fixture を使用するため、Senbei のチェックアウトは不要です。

```powershell
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --workspace --target i686-pc-windows-msvc
```
{% endtab %}

{% tab title="Senbei 1.3.1 オラクル検証" %}
`verification/run_oracle.py` は、パックされた全プロファイルを**無改変の Senbei `1.3.1` チェックアウト**（`version = "=1.3.1"` 固定。`SENBEI_SOURCE` にそれ以降のバージョンの Senbei を指定するとバージョン検査で拒否されます）で検証し、さらに保護前・保護後・アンパック後の各バイナリを実機実行します。実行前に `ARARE_MONO_X86` へ 32ビット版 `mono.exe` の絶対パスを設定してください。また、生成アーティファクトのパスが共有されるため、x64 ターゲットと x86 ターゲットは並列ではなく順番に実行してください。

```powershell
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release --target i686-pc-windows-msvc
```
{% endtab %}

{% tab title="マネージド・GUI スイート" %}
ECMA-335 パーサー／リライターのテスト、マネージドツール探索の単体テスト、および WPF スモークスイートを実行します。

```powershell
python verification/managed/parser_tests.py
cargo test -p arare-engine --lib managed::tool_discovery_tests
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui.SmokeTests -c Release --no-build
```
{% endtab %}
{% endtabs %}

## コントリビューター向けルール

* `arare-pe`、`arare-codec`、およびすべての組み込みランタイムコード（`arare-runtime`、`runtime/`）は純粋な `MIT` ライセンスに保ち、`AGPL-3.0-only` コードを組み込みランタイム側へ絶対に移さないでください。
* 商用のドナーバイナリ、抽出済みスタブ、実サンプルをリポジトリへ持ち込まず、必ず自動生成 fixture のみでテストしてください。
* ファイルオフセットと RVA は別体系の値として厳密に区別し、スライス操作や書き込みの前に両方を検証してください。
* フォーマットを変更した際は、専用の往復デコーダーやセクション除外で済ませず、無改変の Senbei による復元と実 OS 上でのプロセス／DLL 実行で検証してください。
* 設計仕様は `docs/design/`、日付付きの調査記録や計画は `docs/notes/`、利用者向けドキュメントはこの GitBook セクションに配置してください。コミットメッセージに帰属トレーラー（`Co-authored-by` 等）を付与しないでください。
