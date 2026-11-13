# Table of contents

* [CrackProof for Windows 內部機制](README.md)

## 檔案結構 <a href="#file-structure" id="file-structure"></a>

* [概覽](file-structure/file-format.md)
* [容器與加密標頭](file-structure/container-layout.md)
* [識別與建置家族](file-structure/recognition.md)
* [區段資料與伴生檔案](file-structure/companion-layout.md)

## 資料轉換 <a href="#data-transforms" id="data-transforms"></a>

* [概覽](data-transforms/data-transforms.md)
* [滾動金鑰與旋轉加密](data-transforms/rolling-and-rotation.md)
* [LFSR、字串與分頁轉換](data-transforms/lfsr-strings-pages.md)
* [校驗和與金鑰推進](data-transforms/checksums.md)
* [AES-CBC 層](data-transforms/aes.md)
* [Huffman 與 LZ 壓縮](data-transforms/compression.md)
* [依建置產生的位元組轉換](data-transforms/bytecode-transform.md)

## 載入與 PE 修復 <a href="#loading-and-pe-repair" id="loading-and-pe-repair"></a>

* [載入與區段復原](loading-and-pe-repair/loading/README.md)
  * [階段鏈與標記佈局](loading-and-pe-repair/loading/stage-chain.md)
  * [PE32、DLL 與無標記佈局](loading-and-pe-repair/loading/layout-variants.md)
  * [結構探索與驗證](loading-and-pe-repair/loading/discovery-validation.md)
* [PE 重建](loading-and-pe-repair/pe-reconstruction/README.md)
  * [標頭、區段與零填充範圍](loading-and-pe-repair/pe-reconstruction/memory-image.md)
  * [匯入、TLS 與匯出](loading-and-pe-repair/pe-reconstruction/imports-tls-exports.md)
  * [重定位、分頁轉換與 CLR 資料](loading-and-pe-repair/pe-reconstruction/relocations-managed.md)

## 執行階段 <a href="#runtime" id="runtime"></a>

* [概覽](runtime/runtime.md)
* [啟動序列與狀態回報](runtime/startup-status.md)
* [環境與反分析檢查](runtime/environment-checks.md)
* [分頁保護與載入器程式碼](runtime/page-protection.md)
* [手動映射輔助模組](runtime/mapped-modules.md)
* [Htsysm 核心元件](runtime/kernel-components.md)

## 分析 <a href="#analysis" id="analysis"></a>

* [概覽](analysis/analysis.md)
* [分析流程](analysis/workflow.md)
* [實測架構限制](analysis/observed-limitations.md)
* [il2cpp 中繼資料混淆](analysis/il2cpp-metadata.md)
* [常數與偏移](analysis/constants.md)
