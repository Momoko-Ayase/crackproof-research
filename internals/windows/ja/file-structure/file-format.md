---
description: "ディスク上の配置、KONN ヘッダーの判定、ビルド系統の分類、外部コンパニオン分割。"
icon: folder-tree
---

# 保護ファイルの構造

保護された Windows バイナリは、先頭 `0x1000` バイトにロード可能な外側 PE ヘッダーを残し、オフセット `0x1000` に暗号化されたパラメーターヘッダーを配置します。その後続領域（または同一ディレクトリの `._` コンパニオンファイル）には、多段構成のローダーと圧縮済みのアプリケーションセクションが格納されます。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-box-archive"></i></td><td><strong>コンテナと暗号化ヘッダー</strong></td><td>固定境界 <code>0x1000</code> での分割、8 dword の <code>info</code> ヘッダー鍵導出、ペイロード転送範囲。</td><td><a href="container-layout.md">コンテナと暗号化ヘッダー</a></td></tr><tr><td><i class="fa-fingerprint"></i></td><td><strong>フォーマット判定とビルド系統</strong></td><td>データ内容に基づく <code>KONN</code> 検出、PE32 と PE32+ における CLR 判定、レイアウト系統の分類。</td><td><a href="recognition.md">フォーマット判定とビルド系統</a></td></tr><tr><td><i class="fa-copy"></i></td><td><strong>セクションデータとコンパニオンファイル</strong></td><td><code>0x1080</code> のビット反転エンコードされたセクションデータ基準値と、外部 <code>._</code> コンパニオンファイルのペアリングおよびオーバーレイ。</td><td><a href="companion-layout.md">セクションデータとコンパニオンファイル</a></td></tr></tbody></table>
