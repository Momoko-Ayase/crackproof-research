---
description: "保護された Android ELF64 共有ライブラリの識別条件と Stage 1/2 の境界"
icon: folder-tree
---

# ファイル形式

保護された Android 共有ライブラリは、有効なリトルエンディアン ELF64 AArch64 バイナリの形式を保っています。動的リンク関連のセクションはセクションヘッダーテーブル上にそのまま残る一方、ロード対象のコード領域およびデータ領域はファイル末尾に追加された単一の `SHT_LOUSER` 専用セクションへ退避され、元の領域はゼロ埋めされています。

ヘッダー種別、セクションオフセット、パラメーター範囲、および入れ子ストリームの境界はすべて整合している必要があり、いずれか 1 つでも満たさないファイルは対象として受理されません。ロード時に同じ構造を特定する手順については、[Stage 1 ブートストラップ](../runtime/stage1-bootstrap.md)を参照してください。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-file-code"></i></td><td><strong>保護済み ELF</strong></td><td>必須となる ELF64 ヘッダー、動的セクション、<code>.init_array</code> のブートストラップスロット、および APK 内の付随ファイル。</td><td><a href="protected-elf.md">保護済み ELF</a></td></tr><tr><td><i class="fa-box-archive"></i></td><td><strong>Stage 1 ヘッダー</strong></td><td><code>SHT_LOUSER</code> 専用セクションの内部レイアウト、32 バイトのワードヘッダー、および相対オフセット境界。</td><td><a href="stage1.md">Stage 1 ヘッダー</a></td></tr><tr><td><i class="fa-bars-staggered"></i></td><td><strong>Stage 2 ストリーム</strong></td><td><code>0x5C</code> バイトのレコード記述子、直接スライスと子ストリームの分岐、およびコンテナーペイロードのディスパッチ。</td><td><a href="stage2-streams.md">Stage 2 ストリーム</a></td></tr></tbody></table>
