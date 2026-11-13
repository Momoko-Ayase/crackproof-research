---
description: "Stage 1 スタブから多段 Stage 2 インタープリターと環境検査に至るロード時実行。"
icon: play
---

# ランタイム

ロード時、Android の動的リンカーは中抜きされた ELF をメモリへマップして `.init_array` を実行し、Stage 1 ブートストラップスタブへ制御を渡します。Stage 1 は Stage 2（`0xE2`）をマップ・復号し、Stage 2 は 256 スロットのモジュールテーブルを確保して入れ子状のインタープリターストリーム（`0xE2`..`0xE8`）を順に実行します。その過程でユーザー空間の環境検査・整合性チェックを行い、メモリ上の ELF セグメントと再配置を復元したあと、モジュール `0x98` を通じて本来のコンストラクターを呼び出します。

静的復元で必要になるのは、コンテナー・シンボル・再配置・コンストラクター・メタデータを担う各モジュール（`0x9B`、`0x9D`、`0x9E`、および任意の `0x96`、`0x98`、`0x0C`）のみであり、環境検査モジュールは実行時にしか動作しません。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-bolt"></i></td><td><strong>Stage 1 ブートストラップ</strong></td><td><code>/proc/self/maps</code> による自身の特定、<code>SHT_LOUSER</code> の復号、ページサイズ判定、レジスタ引き渡し。</td><td><a href="stage1-bootstrap.md">Stage 1 ブートストラップ</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>Stage 2 インタープリター</strong></td><td>256 スロットのモジュールテーブル、<code>0x5C</code> レコード記述子、多段 <code>0xE2</code>..<code>0xE8</code> ストリーム実行。</td><td><a href="stage2-interpreter.md">Stage 2 インタープリター</a></td></tr><tr><td><i class="fa-user-shield"></i></td><td><strong>環境検査と整合性チェック</strong></td><td>NativeBridge 検出、<code>PTRACE_SEIZE</code> ヘルパープロセス、<code>/proc/&lt;pid&gt;/mem</code> 監視、APK 署名検証。</td><td><a href="environment-checks.md">環境検査と整合性チェック</a></td></tr><tr><td><i class="fa-layer-group"></i></td><td><strong>ランタイムモジュール一覧</strong></td><td>インタープリター、ELF・メタデータ復元、環境検査を担う確認済み Stage 2 モジュール ID の一覧。</td><td><a href="modules.md">ランタイムモジュール一覧</a></td></tr></tbody></table>
