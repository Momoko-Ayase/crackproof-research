---
description: "実践的な解析ワークフロー、設計上の制約、-GMD IL2CPP メタデータ再マッピング、および定数一覧。"
icon: compass
---

# 解析ノート

CrackProof で保護された Windows バイナリの静的・動的解析では、構造の相互検証、デバッグログコードから各ステージ処理への対応付け、および形式ごとの事後検証を組み合わせて進めます。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-check"></i></td><td><strong>解析ワークフロー</strong></td><td>デバッグログの有効化、ステージの特定、ページ保護モジュールのダンプ、PE 出力検証の手順。</td><td><a href="workflow.md">解析ワークフロー</a></td></tr><tr><td><i class="fa-triangle-exclamation"></i></td><td><strong>確認されている制約</strong></td><td>VM 検知、デバッグログ、オンデマンドページ復号、ドライバー、CRC チェーンに関する設計上の制約。</td><td><a href="observed-limitations.md">確認されている制約</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>il2cpp メタデータ難読化</strong></td><td>Unity IL2CPP の Windows <code>-GMD</code> ビルドで疎なトークンに書き換えられた MethodDef を鍵なしで復元する手順。</td><td><a href="il2cpp-metadata.md">il2cpp メタデータ難読化</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>定数とオフセット一覧</strong></td><td>マジック値、コンテナー計算式、PE32/PE32+ フィールドオフセット、バイトコード命令の一覧表。</td><td><a href="constants.md">定数とオフセット一覧</a></td></tr></tbody></table>
