# Table of contents

* [CrackProof for Android SO 內部機制](README.md)

## 檔案格式 <a href="#file-format" id="file-format"></a>

* [概覽](file-format/file-format.md)
* [受保護 ELF](file-format/protected-elf.md)
* [第一階段標頭](file-format/stage1.md)
* [第二階段記錄串流](file-format/stage2-streams.md)

## 資料轉換 <a href="#data-transforms" id="data-transforms"></a>

* [概覽](data-transforms/data-transforms.md)
* [字組、串流與記錄加解密](data-transforms/word-and-record.md)
* [模組設定](data-transforms/module-config.md)
* [容器轉換](data-transforms/container.md)
* [Huffman 與 LZ 壓縮](data-transforms/compression.md)

## 復原 <a href="#restoration" id="restoration"></a>

* [概覽](restoration/restoration.md)
* [模組串流](restoration/module-streams.md)
* [動態連結](restoration/dynamic-linking.md)
* [ELF 輸出](restoration/elf-output.md)

## 執行階段 <a href="#runtime" id="runtime"></a>

* [概覽](runtime/runtime.md)
* [第一階段引導](runtime/stage1-bootstrap.md)
* [第二階段直譯器](runtime/stage2-interpreter.md)
* [環境與完整性檢查](runtime/environment-checks.md)
* [執行階段模組](runtime/modules.md)

## 中繼資料 <a href="#metadata" id="metadata"></a>

* [概覽](metadata/metadata.md)
* [方法 token](metadata/method-tokens.md)
* [儲存佈局](metadata/storage-layouts.md)

## 分析 <a href="#analysis" id="analysis"></a>

* [概覽](analysis/analysis.md)
* [驗證檢核表](analysis/validation.md)
* [格式常數](analysis/constants.md)
