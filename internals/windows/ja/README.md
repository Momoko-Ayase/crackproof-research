---
description: "CrackProof で保護された Windows PE の構造、暗号変換、復元処理、実行時保護。"
icon: desktop
---

# CrackProof for Windows の内部構造

CrackProof for Windows は、PE32（`0x10B`）および PE32+（`0x20B`）の実行ファイル（EXE）と DLL を保護対象とします。保護されたバイナリは、ブートストラップローダーをメモリへマップするための有効な外側 PE 構造を維持しつつ、元のアプリケーションセクション、ローダーステージ、インポート情報や CLR メタデータ、コードページを暗号化・圧縮した状態で保持します。ロード時にはランタイムがホスト環境を検証してメモリイメージを再構築し、設定に応じて実行可能ページを例外ハンドラー配下で保護したうえで、元のエントリポイント（OEP）へ制御を移します。

これまでに確認されているビルドには、ネイティブおよびマネージド（.NET）の EXE・DLL、マーカーあり／マーカーなしの 64 ビットシェル、標準型およびコンパクト型の 32 ビットシェル、64 ビット DLL 専用コンテナ、さらに 4 KiB のスタブと外部 `._` コンパニオンファイルに分割された PE32+ モジュールが存在します。

## 表記規則

* 特に断りがない限り、オフセットはファイル先頭からの 16 進バイトオフセットを表します。`u32@X` はオフセット `X` にあるリトルエンディアンの 32 ビット符号なし整数を指します。
* **RVA**（相対仮想アドレス）は標準の PE 仕様に従います。イメージの再構築は RVA でインデックスされたイメージバッファー上で行われます（64 ビット出力では `VirtualAddress == PointerToRawData` となり、32 ビット出力ではファイルアライメント `0x200` で詰め直されます）。
* 整数演算は x86 の挙動と同じく固定幅 8 ビットまたは 32 ビットの符号なしラップアラウンドで行われます。Python コードでは明示的なビットマスク（`& 0xFF`、`& 0xFFFFFFFF`）を適用しています。
* `info[0..7]` はファイルオフセット `0x1000` から復号される 8 個の 32 ビットワードを表します（[コンテナと暗号化ヘッダー](file-structure/container-layout.md)を参照）。

## セクション

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-folder-tree"></i></td><td><strong>ファイル構造</strong></td><td><code>0x1000</code> 境界のディスク上コンテナ分割、<code>KONN</code> ヘッダーの鍵導出、ビルド系統、外部 <code>._</code> コンパニオンファイル。</td><td><a href="file-structure/file-format.md">保護ファイルの構造</a></td></tr><tr><td><i class="fa-shuffle"></i></td><td><strong>データ変換</strong></td><td>ローリング XOR チェーンとローテーション暗号、LFSR、文字列・ページスクランブル、CRC とステージ鍵導出、AES-CBC、Huffman/LZ 圧縮、バイトコード VM。</td><td><a href="data-transforms/data-transforms.md">データ変換</a></td></tr><tr><td><i class="fa-stairs"></i></td><td><strong>ロード処理とセクション復元</strong></td><td>9 フェーズ構成の 64 ビットステージチェーン、PE32 の標準型・コンパクト型と専用 DLL コンテナ、マーカーなし構造の探索。</td><td><a href="loading-and-pe-repair/loading/README.md">ロード処理とセクション復元</a></td></tr><tr><td><i class="fa-puzzle-piece"></i></td><td><strong>PE 再構築</strong></td><td>セクションヘッダー、一時的な EP・データディレクトリブロック、インポートテーブルと <code>.kmiat</code>、TLS、エクスポートテーブル、再配置、CLR オーバーレイ。</td><td><a href="loading-and-pe-repair/pe-reconstruction/README.md">PE 再構築</a></td></tr><tr><td><i class="fa-play"></i></td><td><strong>ランタイム</strong></td><td>ステータスログ、<code>AAA-BBB-CCC</code> エラーコード、耐解析チェック、<code>KiUserExceptionDispatcher</code> によるページ保護、ヘルパーモジュール、<code>Htsysm</code> ドライバー。</td><td><a href="runtime/runtime.md">ランタイムの挙動</a></td></tr><tr><td><i class="fa-compass"></i></td><td><strong>解析ノート</strong></td><td>静的解析と動的解析のワークフロー、静的復元の制約、<code>-GMD</code> による IL2CPP メタデータの再マッピング、主要オフセット・定数一覧。</td><td><a href="analysis/analysis.md">解析ノート</a></td></tr></tbody></table>

本セクションで解説する各変換の実行可能な Python 実装とテストベクターは、[検証とリファレンス](https://app.gitbook.com/s/UWQkIK86mO8QHm25y3lh/)に収録しています。また、3 バイト形式の Huffman/LZ トークン符号化およびバッファー内 AES 鍵スケジュールは、[CrackProof for Android SO の内部構造](https://app.gitbook.com/s/Uiv7ZqRm9GbUFbENk158/)でも共通して使用されています。
