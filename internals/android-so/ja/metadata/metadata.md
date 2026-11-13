---
description: "Android 版 IL2CPP メタデータのメソッドトークン・methodIndex 置換と格納方式。"
icon: database
---

# メタデータ

Unity IL2CPP 採用の Android ビルドでは、CrackProof は `libil2cpp.so` とあわせて `global-metadata.dat` も保護します。メタデータのバージョンやパッケージング形式に応じて、外部 `global-metadata.dat` 内のメソッドトークンまたは `methodIndex` フィールドを置換する方式（実行時にはモジュール `0x0C` の `mmap` フックで復元）と、`.so` のデータセクション内に 32 ビット XOR キーでマスクしたスリム版バージョン 24 メタデータブロブを埋め込む方式の 2 通りが存在します。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-hashtag"></i></td><td><strong>メソッドトークン</strong></td><td>バージョン 29・31・39 の 5 ラウンド逆置換、v31 のテーブル順（<code>-GMD</code>）再割り当て、v24.1 の <code>methodIndex</code> 復元。</td><td><a href="method-tokens.md">メソッドトークン</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>格納レイアウト</strong></td><td>外部 <code>global-metadata.dat</code> のパッケージ対応付け規則と、XOR マスク付き埋め込みスリム v24 ブロブ。</td><td><a href="storage-layouts.md">格納レイアウト</a></td></tr></tbody></table>
