---
description: "CrackProof の保護フォーマットと実行時挙動に関する独立した技術調査ドキュメント。"
icon: house
layout:
  width: wide
  title:
    visible: true
  description:
    visible: true
  tableOfContents:
    visible: false
  outline:
    visible: false
  pagination:
    visible: false
  metadata:
    visible: false
  tags:
    visible: true
  actions:
    visible: false
---

# CrackProof 技術調査

CrackProof® は HyperTech が開発する商用バイナリ保護システムの製品群です。本サイトでは、独自に検証したファイルフォーマット、データ変換、多段ローダー、および実行時コンポーネントの内部仕様をまとめています。

調査対象は Windows PE ファイル（CrackProof for Windows®）および Android AArch64 共有ライブラリです。プラットフォームごとにコンテナー構造と復元パイプラインが異なるため、内部仕様はセクションを分けて解説しています。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-desktop"></i></td><td><strong>Windows の内部構造</strong></td><td>保護された PE のレイアウト、暗号処理、多段ロード、PE 再構築、および実行時チェック。</td><td><a href="https://app.gitbook.com/s/DDUo0VKfH9uzyTcguGIx/">CrackProof for Windows® の内部構造</a></td></tr><tr><td><i class="fa-mobile-screen-button"></i></td><td><strong>Android SO の内部構造</strong></td><td>保護された AArch64 ELF のレイアウト、ネストされたモジュールストリーム、コンテナー復号、ELF 復元、および IL2CPP メタデータ。</td><td><a href="https://app.gitbook.com/s/Uiv7ZqRm9GbUFbENk158/">CrackProof for Android SO の内部構造</a></td></tr><tr><td><i class="fa-code"></i></td><td><strong>検証とリファレンス</strong></td><td>Windows 向け変換処理の実行可能なテストベクター、Python リファレンス実装、および匿名化したデバッグログ。</td><td><a href="https://app.gitbook.com/s/UWQkIK86mO8QHm25y3lh/">検証とリファレンス</a></td></tr><tr><td><i class="fa-screwdriver-wrench"></i></td><td><strong>Senbei</strong></td><td>保護された Windows PE ファイル、Android 共有ライブラリ、IL2CPP メタデータに対応する静的アンパッカー（CLI、デスクトップ GUI、設計、開発）。</td><td><a href="https://app.gitbook.com/s/ztt8mmT5fZLnHqBjw6QU/">Senbei</a></td></tr><tr><td><i class="fa-shield-halved"></i></td><td><strong>Arare</strong></td><td>観測されたレイアウト系統を再現するソースビルドの Windows PE プロテクター（CLI、GUI、対応マトリクス、設計、開発）。</td><td><a href="https://app.gitbook.com/s/9ZgUU6f4YpWlyjh6KdQl/">Arare</a></td></tr></tbody></table>

## 調査範囲

本サイトに記載している規則はすべて、観測可能なバイナリ構造と実行時の挙動に基づいています。フィールド名やコンポーネント名には、バイナリ内の文字列、デバッグログ出力、プラットフォームの標準仕様、またはバイト列の動作をそのまま表す名称を用いています。複数のサンプルで共通して確認できる挙動や、内部の整合性チェックで必須とされている仕様のみをフォーマットの一般規則として扱っています。

調査セクション全体を通じて、保護対象の製品名、導入環境ごとのドライバーファイル名、サンプルを特定し得るパスは記載していません。Senbei と Arare については、それぞれ独立した製品セクションで解説しています。

{% hint style="warning" %}
**法的通知:** 本資料は、ご自身が所有するバイナリ、または解析の明示的な許諾を得たバイナリに対してのみ使用してください。技術的保護手段の回避に関する法令およびライセンス契約の定めは法域によって異なります。本サイトは独立した技術資料であり、ベンダーのソースコードや鍵は一切含まず、HyperTech とは一切関係ありません。また、復元したバイナリの再配布を許諾するものではありません。
{% endhint %}
