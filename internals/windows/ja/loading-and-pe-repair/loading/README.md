---
description: "自己復号ローダーステージ連鎖、レイアウト派生、試行検証によるセクション復元の仕組み。"
icon: stairs
---

# ローディングとセクション復元

保護された Windows バイナリは、5 段から 8 段の自己復号ローダーステージを連鎖的に実行します。各ステージの復号には前段の CRC-32 チェックサム、三角数による鍵更新、およびビルド別のバイトコードスタブが使われ、すべてのステージを展開すると最終的なセクション復元テーブルが得られます。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-link"></i></td><td><strong>ステージ連鎖とマーカーありレイアウト</strong></td><td>複合ステージ復号器と、64 ビットのマーカーありレイアウトにおける 9 フェーズのセクション復元パイプライン。</td><td><a href="stage-chain.md">ステージ連鎖とマーカーありレイアウト</a></td></tr><tr><td><i class="fa-code-branch"></i></td><td><strong>PE32・DLL・マーカーなしレイアウト</strong></td><td>標準 / コンパクト PE32 シェル、専用 64 ビット DLL の固定テーブル、マーカーなし 64 ビットビルドの探索手法。</td><td><a href="layout-variants.md">PE32・DLL・マーカーなしレイアウト</a></td></tr><tr><td><i class="fa-magnifying-glass"></i></td><td><strong>構造探索と妥当性検証</strong></td><td>試行復号、圧縮ブロックによる検証、および <code>.text</code> ページスクランブルの選択ルール。</td><td><a href="discovery-validation.md">構造探索と妥当性検証</a></td></tr></tbody></table>
