---
description: "CrackProof 所保護 Android 原生庫的內部結構與恢復規則。"
---

# CrackProof for Android SO 內部機制

本 Space 記錄 CrackProof Android 原生庫格式，範圍包括 ELF64 小端 AArch64 文件、私有保護節、分階段記錄流，以及重建可用 ELF 鏡像所需的結構。

它與 Windows 版本屬於同一產品家族，但不是 PE 格式的變體。Android 的識別條件、節佈局、記錄流和元數據規則單獨說明。

## 內容導航

| 分區 | 內容 |
| --- | --- |
| [文件格式](file-format/README.md) | ELF 識別、私有節和兩階段記錄流 |
| [數據變換](data-transforms/README.md) | 外層首部、模塊配置、容器變換和壓縮 |
| [恢復](restoration/README.md) | 記錄分發、動態鏈接和 ELF 輸出 |
| [元數據](metadata/README.md) | IL2CPP 方法令牌和元數據存儲方式 |
| [分析](analysis/README.md) | 校驗規則、失敗處理和已觀察常量 |

Windows PE 格式請參閱 [Windows internals Space](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A)。

本文檔是研究參考，記錄已觀察到的結構和校驗行為，不提供產品操作流程或通用解包步驟。
