---
description: "Stage 2 モジュールを抽出し、動的テーブルを再構築して正常な ELF64 を出力する"
icon: puzzle-piece
---

# 復元

静的復元は 2 段階で進みます。まず `SHT_LOUSER` 専用セクションから Stage 2 のモジュール群を抽出し、続いて ELF のロードセグメント、動的リンク用の各テーブル、およびセクションヘッダーテーブルを再構築した上で出力イメージを検証します。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-route"></i></td><td><strong>モジュールストリーム</strong></td><td>必須の基本モジュール（<code>0x9B</code>、<code>0x9D</code>、<code>0x9E</code>）と任意の静的復元モジュール（<code>0x96</code>、<code>0x98</code>、<code>0x0C</code>）。</td><td><a href="module-streams.md">モジュールストリーム</a></td></tr><tr><td><i class="fa-link"></i></td><td><strong>動的リンク</strong></td><td>非公開シンボルの復元、<code>0x96</code> によるシンボル置換の解除、省略された <code>libc</code> PLT スロットの補完、コンストラクター復元、および <code>PT_LOAD</code> の配置。</td><td><a href="dynamic-linking.md">動的リンク</a></td></tr><tr><td><i class="fa-file-export"></i></td><td><strong>ELF 出力</strong></td><td><code>SHT_LOUSER</code> の除去、<code>e_entry</code> のクリア、非 ALLOC セクションの再配置、および必須検証と診断チェック。</td><td><a href="elf-output.md">ELF 出力</a></td></tr></tbody></table>
