---
description: CrackProof 所保護 Android 原生庫的內部結構與恢復規則。
---

# CrackProof for Android SO 內部機制

本 Space 記錄 CrackProof Android 原生庫格式，範圍包括 ELF64 小端 AArch64 文件、私有保護節、分階段記錄流，以及重建可用 ELF 鏡像所需的結構。

它與 Windows 版本屬於同一產品家族，但不是 PE 格式的變體。Android 的識別條件、節佈局、記錄流和元數據規則單獨說明。

## 內容導航

| 分區                                         | 內容                   |
| ------------------------------------------ | -------------------- |
| [文件格式](file-format/file-format.md)         | ELF 識別、私有節和兩階段記錄流    |
| [數據變換](data-transforms/data-transforms.md) | 外層首部、模塊配置、容器變換和壓縮    |
| [恢復](restoration/restoration.md)           | 記錄分發、動態鏈接和 ELF 輸出    |
| [運行時](runtime/runtime.md)                  | 第一階段引導、第二階段解釋器與運行時模塊 |
| [元數據](metadata/metadata.md)                | IL2CPP 方法令牌和元數據存儲方式  |
| [分析](analysis/analysis.md)                 | 校驗規則、失敗處理和已觀察常量      |

Windows PE 格式請參閱 [Windows internals Space](https://app.gitbook.com/o/-Lx9XUuXVg8x3nx7ouIX/s/sFi4W2Zr1UBoxZd5YI3A/)。Huffman/LZ 記號語言與緩衝區內 AES 日程與該家族共享；詞密碼、記錄洋蔥與輔助庫佈局則不是。
