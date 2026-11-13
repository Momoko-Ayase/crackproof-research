---
description: "起動シーケンス、ステータスコード、耐解析検査、ページ保護、手動マップ DLL、Htsysm ドライバ"
icon: play
---

# ランタイム動作

保護された Windows バイナリは実行時、本来のエントリポイント（OEP、ステータス `280`）へジャンプする前に CrackProof のブートストラップローダーを実行します。ローダーは条件付きのデバッグログ出力、補助 DLL のメモリ上への手動マップ、OS・VM・デバッガ・プロセス環境の検査、必要に応じた `Htsysm` カーネルドライバの初期化、セクションとインポートの再構築を行い、設定によっては実行ページを再暗号化したうえで `KiUserExceptionDispatcher` フックによるオンデマンド復号で保護します。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-ol"></i></td><td><strong>起動シーケンスとステータス通知</strong></td><td>12 ビットの起動ステータスコード、<code>%temp%</code> の 16 進 12 桁フォルダゲート、<code>ErrLog-Pec</code> メールスロット、<code>AAA-BBB-CCC</code> 終了コード。</td><td><a href="startup-status.md">起動シーケンスとステータス通知</a></td></tr><tr><td><i class="fa-user-shield"></i></td><td><strong>実行環境・耐解析チェック</strong></td><td>デバッガ、VM、ブート設定、注入 DLL・外部スレッド、<code>A11</code>/<code>A15</code> ホスト検証、システム DLL のアンフック処理。</td><td><a href="environment-checks.md">実行環境・耐解析チェック</a></td></tr><tr><td><i class="fa-lock"></i></td><td><strong>ページ保護とローダーコード</strong></td><td><code>KiUserExceptionDispatcher</code> によるオンデマンドページ復号、scribble、ポリモーフィック変形、デコイ、ディスクからの自ファイルマッピング。</td><td><a href="page-protection.md">ページ保護とローダーコード</a></td></tr><tr><td><i class="fa-layer-group"></i></td><td><strong>手動マップされる補助モジュール</strong></td><td>埋め込み補助 DLL（<code>it</code>、<code>dt</code>、<code>cm</code>、<code>dm</code>、<code>sk</code>、<code>pm</code>）の役割と PEB モジュールリストに残らない理由。</td><td><a href="mapped-modules.md">手動マップされる補助モジュール</a></td></tr><tr><td><i class="fa-gears"></i></td><td><strong>Htsysm カーネルコンポーネント</strong></td><td>第 1 から第 3 世代の変遷（<code>Htsysm</code>、<code>Htsysm7679</code>、<code>Htsysm1B4001</code> を含む <code>0xAA02</code> <code>ObRegisterCallbacks</code> ドライバ）。</td><td><a href="kernel-components.md">Htsysm カーネルコンポーネント</a></td></tr></tbody></table>
