---
description: "CrackProof のレイアウト系統を再現するソースビルドの Windows PE プロテクター。"
icon: shield-halved
---

# Arare

Arare はソースコードからビルドされる Windows PE プロテクターです。商用のドナーバイナリや抽出済みのスタブプロファイルを一切使用せず、独自のネイティブ／マネージドローダーをコンパイルし、ビルドごとの鍵、AES スケジュール、バイトコードプログラム、Huffman/LZ 圧縮テーブル、各ステージのメタデータを生成します。

ネイティブ保護は4種類のレイアウト系統（`pe32`、`pe64-classic`、`pe64-modern`、`legacy-dll`）で x86 および x64 の EXE と DLL に対応します。マネージド保護は、自動生成された ECMA-335 起動用型と独立したネイティブデコーダーで IL アセンブリをラップします。互換性については、無改変の Senbei 1.3.1 による復元検証と、Windows 11 ビルド 26100 上での保護前・保護後・アンパック後バイナリの実機実行で確認しています（ターゲット OS は Windows 10 および Windows 11）。

組み込みランタイムは、ビルド固有の `%TEMP%` フォルダーによるデバッグログ制御、手動マップされるヘルパー DLL 内での構成可能な環境チェック、`KiUserExceptionDispatcher` を用いたオンデマンドページ復号（ページ暗号化）、シードに基づくローダーコード変形、起動完了後のメタデータ消去を実装しています。チェック失敗時には、ログ出力が有効な場合に `AAA-BBB-CCC` の終了コードを記録します。ネイティブ EXE では既定（`--antidebug-av=on`）で終了前に `EXCEPTION_ACCESS_VIOLATION` を発生させてアタッチ中のデバッガーをブレークさせ、DLL、`--antidebug-av=off` 指定のネイティブ EXE、およびマネージドモジュールでは直接 `TerminateProcess` を呼び出します。

ベースとなるフォーマット仕様については [CrackProof for Windows の内部構造](https://app.gitbook.com/s/XSPACE_WINDOWS_JA/)を参照してください。静的アンパックについては [Senbei](https://app.gitbook.com/s/XSPACE_SENBEI_JA/) で解説しています。

## このセクションの内容

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-terminal"></i></td><td><strong>使い方</strong></td><td>CLI の <code>protect</code>・<code>inspect</code>・<code>verify</code> コマンド、プロファイル、環境チェック、ページ暗号化、デバッグログ。</td><td><a href="usage.md">使い方</a></td></tr><tr><td><i class="fa-window-maximize"></i></td><td><strong>GUI</strong></td><td>バッチジョブキュー、行単位のプロファイル・チェック上書き、PowerShell スクリプト出力、検証を行う WPF フロントエンド。</td><td><a href="gui.md">GUI</a></td></tr><tr><td><i class="fa-circle-check"></i></td><td><strong>対応範囲</strong></td><td>対応するネイティブ・マネージド系統、検証済み CLR ホスト、パック時の拒否条件、構造上の上限。</td><td><a href="support.md">対応範囲</a></td></tr><tr><td><i class="fa-diagram-project"></i></td><td><strong>設計</strong></td><td>クレート境界、重複を持たないセクション・リソース符号化、3段階の実行時起動フロー、商用版との残存差分。</td><td><a href="design.md">設計</a></td></tr><tr><td><i class="fa-hammer"></i></td><td><strong>開発</strong></td><td>ネイティブローダーとマネージドツールのビルド、Senbei 1.3.1 オラクルの実行、ワークスペース規約。</td><td><a href="development.md">開発</a></td></tr></tbody></table>

## 対象範囲とライセンス

Android ターゲット、単体の IL2CPP `global-metadata.dat` 難読化、および `protect` コマンドにおけるカーネルドライバーオプションは対象外です（実験的なカーネルプロバイダーは `kernel/` 配下に独立して配置されています）。

{% hint style="info" %}
**ライセンスの分離:** ホスト側ツール群（`arare-cli`、`arare-engine`、`tools/managed`、`gui`、`verification/senbei-oracle`）は `AGPL-3.0-only` です。一方、PE パーサー（`arare-pe`）、コーデック（`arare-codec`）、およびすべての組み込みネイティブ／マネージドランタイムコード（`arare-runtime`、`runtime/`）は `MIT` ライセンスであり、保護後のバイナリに AGPL コードが組み込まれることはありません。
{% endhint %}
