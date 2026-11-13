---
description: "CrackProof 保護バイナリ（PE・Android SO・IL2CPP）の静的アンパッカー。"
icon: screwdriver-wrench
---

# Senbei

Senbei（`1.4.0`）は、CrackProof で保護されたバイナリ向けの静的アンパッカーおよび構造検査ツールです。ターゲットを実行したりプロセスへアタッチしたりすることなく、単体ファイル、Android アプリパッケージ、ディレクトリからバイナリを復元・検証します。

Windows および Linux 向けのネイティブリリースには、コマンドラインツールの `senbei` とデスクトップワークベンチの `senbei-gui` が同梱されており、英語・簡体字中国語・繁体字中国語・日本語・韓国語の5言語に対応しています。同じコアエンジンを WebAssembly にビルドしたブラウザー版では、単体の Windows PE ファイルおよびメタデータファイルをローカル環境のまま処理できます。

## 対応入力

* **Windows PE（`PE32` および `PE32+`）:** 保護された `.exe` および `.dll` モジュール（ネイティブおよびマネージド .NET）。外部の `.exe._` / `.dll._` コンパニオンファイルを伴う構成にも対応します。
* **Android ネイティブライブラリ（`ELF64` AArch64）:** 単体の保護された `.so` ファイル、および `.apk`・`.apks`・`.xapk` アプリパッケージ。
* **Unity IL2CPP メタデータ:** Windows の `-GMD`（`v31`）、および Android のシード派生型（`v24.1`、`v29`、`v31`、`v39`）または埋め込み XOR 型（`v24`）レイアウトの `global-metadata.dat` ファイル。

対象となるコンテナーフォーマットとデータ変換の詳細は、[CrackProof for Windows の内部構造](https://app.gitbook.com/s/XSPACE_WINDOWS_JA/)および[CrackProof for Android SO の内部構造](https://app.gitbook.com/s/XSPACE_ANDROID_JA/)を参照してください。

## このセクションの内容

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-terminal"></i></td><td><strong>使い方</strong></td><td>CLI コマンド（<code>unpack</code>、<code>inspect</code>、<code>--dry-run</code>、<code>--json</code>）、フォルダーとパッケージの処理規則、表示言語、フラグ、終了コード。</td><td><a href="usage.md">使い方</a></td></tr><tr><td><i class="fa-window-maximize"></i></td><td><strong>GUI</strong></td><td>ネイティブデスクトップワークベンチ（<code>senbei-gui</code>）：バッチキュー、解析詳細ビュー、Hex + RVA ビューアー、PE 比較、設定。</td><td><a href="gui.md">GUI</a></td></tr><tr><td><i class="fa-diagram-project"></i></td><td><strong>設計</strong></td><td>9クレート構成のワークスペース、プロファイルとトレース構造、Windows・Android パイプライン、WebAssembly の境界設計。</td><td><a href="design.md">設計</a></td></tr><tr><td><i class="fa-hammer"></i></td><td><strong>開発</strong></td><td>CLI・デスクトップ GUI・WebAssembly のビルド手順、コーパス・ファジング・パリティ検証スイート、ベンチマーク、環境変数。</td><td><a href="development.md">開発</a></td></tr></tbody></table>

## インターフェース一覧

| インターフェース | 対応ターゲット | 出力・レポート機能 |
| --- | --- | --- |
| `senbei`（CLI） | 単体ファイル、フォルダー、`.apk`/`.apks`/`.xapk` | 復元ファイル、実行ログ、カラー端末出力、`--json` スキーマ v1 レポート |
| `senbei-gui`（デスクトップ） | 単体ファイル、フォルダー、`.apk`/`.apks`/`.xapk` | 復元ファイル、対話型の **概要** / **解析詳細** / **Hex** / **比較** / **エントリ** / **ログ** ビュー、JSON・テキストレポート出力 |
| ブラウザー版（`web/`） | 単体の Windows PE ファイル（`._` コンパニオンを含む）および `global-metadata.dat` | ブラウザー上でのファイル保存および `Export JSON` レポート（入力データは外部へ送信されません） |
