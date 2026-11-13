# Table of contents

* [CrackProof for Windows 内部構造](README.md)

## ファイル構造 <a href="#file-structure" id="file-structure"></a>

* [概要](file-structure/file-format.md)
* [コンテナーと暗号化ヘッダー](file-structure/container-layout.md)
* [識別とビルドファミリー](file-structure/recognition.md)
* [セクションデータとコンパニオンファイル](file-structure/companion-layout.md)

## データ変換 <a href="#data-transforms" id="data-transforms"></a>

* [概要](data-transforms/data-transforms.md)
* [ローリングキー暗号とローテーション暗号](data-transforms/rolling-and-rotation.md)
* [LFSR・文字列・ページ変換](data-transforms/lfsr-strings-pages.md)
* [チェックサムと鍵の更新](data-transforms/checksums.md)
* [AES-CBC レイヤー](data-transforms/aes.md)
* [Huffman / LZ 圧縮](data-transforms/compression.md)
* [ビルド固有のバイト変換](data-transforms/bytecode-transform.md)

## ロードとPE修復 <a href="#loading-and-pe-repair" id="loading-and-pe-repair"></a>

* [ロードとセクション復元](loading-and-pe-repair/loading/README.md)
  * [ステージチェーンとマーカー方式](loading-and-pe-repair/loading/stage-chain.md)
  * [PE32・DLL・マーカーなしレイアウト](loading-and-pe-repair/loading/layout-variants.md)
  * [構造探索と検証](loading-and-pe-repair/loading/discovery-validation.md)
* [PE 再構築](loading-and-pe-repair/pe-reconstruction/README.md)
  * [ヘッダー・セクション・ゼロ埋め範囲](loading-and-pe-repair/pe-reconstruction/memory-image.md)
  * [インポート・TLS・エクスポート](loading-and-pe-repair/pe-reconstruction/imports-tls-exports.md)
  * [再配置・ページ変換・CLR データ](loading-and-pe-repair/pe-reconstruction/relocations-managed.md)

## ランタイム <a href="#runtime" id="runtime"></a>

* [概要](runtime/runtime.md)
* [起動シーケンスとステータスコード](runtime/startup-status.md)
* [環境検査と耐解析チェック](runtime/environment-checks.md)
* [ページ保護とローダーコード](runtime/page-protection.md)
* [手動マップされる補助モジュール](runtime/mapped-modules.md)
* [Htsysm カーネルコンポーネント](runtime/kernel-components.md)

## 解析 <a href="#analysis" id="analysis"></a>

* [概要](analysis/analysis.md)
* [解析ワークフロー](analysis/workflow.md)
* [確認されている制約](analysis/observed-limitations.md)
* [il2cpp メタデータ難読化](analysis/il2cpp-metadata.md)
* [定数とオフセット一覧](analysis/constants.md)
