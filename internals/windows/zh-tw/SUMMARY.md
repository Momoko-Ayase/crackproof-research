# Table of contents

* [CrackProof for Windows 內部機制](README.md)

## 文件結構 <a href="#file-structure" id="file-structure"></a>

* [概覽](file-structure/file-format.md)
* [容器與加密頭](file-structure/container-layout.md)
* [識別與構建家族](file-structure/recognition.md)
* [節數據與伴生文件](file-structure/companion-layout.md)

## 數據變換 <a href="#data-transforms" id="data-transforms"></a>

* [概覽](data-transforms/data-transforms.md)
* [滾動密鑰與旋轉密碼](data-transforms/rolling-and-rotation.md)
* [LFSR、字符串與頁變換](data-transforms/lfsr-strings-pages.md)
* [校驗和與密鑰推進](data-transforms/checksums.md)
* [AES-CBC 層](data-transforms/aes.md)
* [Huffman 與 LZ 壓縮](data-transforms/compression.md)
* [按構建定製的字節變換](data-transforms/bytecode-transform.md)

## 加載與 PE 修復 <a href="#loading-and-pe-repair" id="loading-and-pe-repair"></a>

* [加載與節恢復](loading-and-pe-repair/loading/README.md)
  * [階段鏈與標記佈局](loading-and-pe-repair/loading/stage-chain.md)
  * [PE32、DLL 與無標記佈局](loading-and-pe-repair/loading/layout-variants.md)
  * [結構發現與驗證](loading-and-pe-repair/loading/discovery-validation.md)
* [PE 重建](loading-and-pe-repair/pe-reconstruction/README.md)
  * [頭、節與零填充範圍](loading-and-pe-repair/pe-reconstruction/memory-image.md)
  * [導入、TLS 與導出](loading-and-pe-repair/pe-reconstruction/imports-tls-exports.md)
  * [重定位、頁變換與 CLR 數據](loading-and-pe-repair/pe-reconstruction/relocations-managed.md)

## 運行時 <a href="#runtime" id="runtime"></a>

* [概覽](runtime/runtime.md)
* [啟動序列與狀態報告](runtime/startup-status.md)
* [環境與反分析檢查](runtime/environment-checks.md)
* [頁保護與加載器代碼](runtime/page-protection.md)
* [手動映射輔助模塊](runtime/mapped-modules.md)
* [Htsysm 內核組件](runtime/kernel-components.md)

## 分析 <a href="#analysis" id="analysis"></a>

* [概覽](analysis/analysis.md)
* [分析流程](analysis/workflow.md)
* [已觀察到的侷限](analysis/observed-limitations.md)
* [il2cpp 元數據混淆](analysis/il2cpp-metadata.md)
* [常量與偏移](analysis/constants.md)
