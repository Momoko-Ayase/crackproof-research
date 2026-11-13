# Table of contents

* [CrackProof for Android SO 内部構造](README.md)

## ファイル形式 <a href="#file-format" id="file-format"></a>

* [概要](file-format/file-format.md)
* [保護された ELF](file-format/protected-elf.md)
* [ステージ1ヘッダー](file-format/stage1.md)
* [ステージ2ストリーム](file-format/stage2-streams.md)

## データ変換 <a href="#data-transforms" id="data-transforms"></a>

* [概要](data-transforms/data-transforms.md)
* [ワード・ストリーム・レコード暗号](data-transforms/word-and-record.md)
* [モジュール設定](data-transforms/module-config.md)
* [コンテナー変換](data-transforms/container.md)
* [Huffman / LZ 圧縮](data-transforms/compression.md)

## 復元 <a href="#restoration" id="restoration"></a>

* [概要](restoration/restoration.md)
* [モジュールストリーム](restoration/module-streams.md)
* [動的リンク](restoration/dynamic-linking.md)
* [ELF 出力](restoration/elf-output.md)

## ランタイム <a href="#runtime" id="runtime"></a>

* [概要](runtime/runtime.md)
* [ステージ1ブートストラップ](runtime/stage1-bootstrap.md)
* [ステージ2インタープリター](runtime/stage2-interpreter.md)
* [環境検査と整合性チェック](runtime/environment-checks.md)
* [ランタイムモジュール](runtime/modules.md)

## メタデータ <a href="#metadata" id="metadata"></a>

* [概要](metadata/metadata.md)
* [メソッドトークン](metadata/method-tokens.md)
* [格納レイアウト](metadata/storage-layouts.md)

## 解析 <a href="#analysis" id="analysis"></a>

* [概要](analysis/analysis.md)
* [検証チェックリスト](analysis/validation.md)
* [定数一覧](analysis/constants.md)
