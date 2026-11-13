---
description: "実行可能な Python リファレンス実装、テストベクター、ドキュメント検証器、匿名化デバッグログ。"
icon: flask
---

# 検証とリファレンス

このセクションでは、[CrackProof for Windows の内部構造](https://app.gitbook.com/s/XSPACE_WINDOWS_JA/)の裏付けとなる実行可能なリファレンス実装とテストベクター一式、および匿名化した実行時デバッグログを収録しています。

## 検証スイート

このリポジトリに含まれる Windows 向けデータ変換の実装は、次の2つの自動テストで検証されます。

* **`run_tests.py`（31項目比較）:** `verification/` 配下のスタンドアロン Python モジュールを実行し、`vectors.txt` に記録された 25 件の正解レコード（`rust_vectors.rs` で生成）と照合します。
* **`verify_docs.py`（5言語・80 Python ブロック・135項目比較）:** 5つの言語版（`en`、`zh-cn`、`zh-tw`、`ja`、`ko`）それぞれについて、データ変換を解説する9ページから全 16 個の Python コードブロックを抽出して実行し、1言語あたり 27 件のベクター比較を行います。

```bash
python verification/run_tests.py
python verification/verify_docs.py
```

正常終了時の最終出力はそれぞれ `all vectors match` および `all Windows doc snippets verified (5 languages, 80 Python blocks, 135 checks)` です。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-code"></i></td><td><strong>primitives.py</strong></td><td>ローリング XOR チェーン、ローテーション、LFSR、文字列暗号、ページスクランブル、オンデマンドページ暗号、CRC-32、三角鍵スケジュール。</td><td><a href="primitives.py.md">primitives.py</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>aes_impl.py</strong></td><td>バッファー内スケジュールと GF(2⁸) 逆 T-table を用いたゼロ IV AES-CBC 復号。</td><td><a href="aes_impl.py.md">aes_impl.py</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>huffman.py</strong></td><td>3バイトノード形式の Huffman 木デコーダーと4モード（リテラル／ランレングス充填／LZ）展開器。</td><td><a href="huffman.py.md">huffman.py</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>bytecode_vm.py</strong></td><td>ビルドごとに生成される9オペコード <code>AL</code> x86 スタブのパーサー、インタープリター、256バイト LUT ビルダー、および逆変換器。</td><td><a href="bytecode_vm.py.md">bytecode_vm.py</a></td></tr><tr><td><i class="fa-fingerprint"></i></td><td><strong>detect.py</strong></td><td>内容ベースの <code>KONN</code> ヘッダー KDF 認識と PE32/PE32+ ネイティブ・マネージド種別判定。</td><td><a href="detect.py.md">detect.py</a></td></tr><tr><td><i class="fa-circle-check"></i></td><td><strong>run_tests.py</strong></td><td><code>vectors.txt</code> と照合する31項目比較のスタンドアロンテストランナー。</td><td><a href="run_tests.py.md">run_tests.py</a></td></tr><tr><td><i class="fa-list-check"></i></td><td><strong>verify_docs.py</strong></td><td>5言語版 Markdown から Python コードを抽出・実行する検証スクリプト（80ブロック・135チェック）。</td><td><a href="verify_docs.py.md">verify_docs.py</a></td></tr><tr><td><i class="fa-gears"></i></td><td><strong>rust_vectors.rs</strong></td><td>正解データ <code>vectors.txt</code> を生成する独立した Rust 移植実装。</td><td><a href="rust_vectors.rs.md">rust_vectors.rs</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>vectors.txt</strong></td><td>名前付きの16進データおよび構造テストレコード全25件。</td><td><a href="vectors.txt.md">vectors.txt</a></td></tr><tr><td><i class="fa-file-lines"></i></td><td><strong>サンプルデバッグログ</strong></td><td>ページ暗号化されたホスト EXE、ネイティブプラグイン DLL、およびマネージド DLL から採取した匿名化済みの実行時トレース。</td><td><a href="sample-debug-logs.md">サンプルデバッグログ</a></td></tr></tbody></table>
