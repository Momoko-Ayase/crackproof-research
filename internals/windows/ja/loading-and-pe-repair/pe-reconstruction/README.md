---
description: "セクションヘッダー、EP、データディレクトリ、インポート、TLS、再配置、CLRの再構築。"
icon: puzzle-piece
---

# PE 再構築

セクション復元が完了した時点では、RVA でインデックスされたメモリバッファー（`SizeOfImage` バイト）が得られます。これを実際にロード可能な正規の PE ファイルへ戻すには、ビルドのレイアウト系統に応じて、クリア・差し替えられたヘッダーフィールド、インポートテーブル、TLS 情報、エクスポートテーブル、ベース再配置、CLR メタデータの復元と、`.text` ページスクランブルの解除を行う必要があります。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-memory"></i></td><td><strong>ヘッダー・セクション・ゼロ充填範囲</strong></td><td>RVA 配置のセクションヘッダー、32 ビット出力のディスク配置への詰め直し、一時復号される EP / データディレクトリブロック、<code>.bss</code> ゼロ充填チェーン。</td><td><a href="memory-image.md">ヘッダー・セクション・ゼロ充填範囲</a></td></tr><tr><td><i class="fa-sitemap"></i></td><td><strong>インポート・TLS・エクスポート</strong></td><td>系統別のインポート復元、<code>.kmiat</code> の再構築、TLS の復元とベース再配置の再有効化、スタブからのエクスポート復元。</td><td><a href="imports-tls-exports.md">インポート・TLS・エクスポート</a></td></tr><tr><td><i class="fa-cubes"></i></td><td><strong>ベース再配置・ページ変換・CLR データ</strong></td><td><code>/FIXED</code> と ASLR の再配置ポリシー、<code>.text</code> スクランブルの実行順序、CLR メタデータのピンポイント復元。</td><td><a href="relocations-managed.md">ベース再配置・ページ変換・CLR データ</a></td></tr></tbody></table>
