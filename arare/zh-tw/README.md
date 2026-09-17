---
description: "源碼生成的 Windows PE 保護器，復現已觀察到的 CrackProof 佈局族。"
---

# Arare

Arare 是源碼生成的 Windows PE 保護器。它自行生成加載器、密鑰、AES 日程、字節程序、壓縮表與階段元數據。沒有商用供體可執行文件，也沒有抽出的 stub 配置。

原生保護覆蓋 x86 EXE/DLL 與 x64 EXE/DLL，對應 PE32、經典 PE32+、現代 PE32+ 與遺留 DLL 族。託管保護使用可讀的 IL 入口包裝與獨立的原生解碼器。兼容性對照未改動的 Senbei 檢查，並通過執行生成的原始、受保護與恢復後的程序驗證。不以商用字節一致為目標。

目標平臺是 Windows 10 與 Windows 11。當前執行證據來自 Windows 11 內部版本 26100。運行時行為跟隨已觀察的 CrackProof 流水線：按構建門控的調試日誌（使用原始狀態碼）、可配置的環境與反分析檢查（由手動映射的支持模塊運行）、按需解密的頁加密、由種子決定的加載器代碼變化，以及用盡後的運行時元數據擦除。檢查失敗時以 `AAA-BBB-CCC` 失敗碼靜默結束。

這些輸出所對應的保護格式與運行時行為記錄在 [CrackProof Windows 內部機制](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/)。本項目的靜態解包器 Senbei 記錄在 [Senbei](https://app.gitbook.com/s/v6LkixcUwwnaXW5PFCVE/)。

Android、作為打包選項的內核組件，以及獨立的 IL2CPP 元數據混淆均延後。源碼樹中有實驗性內核提供程序；它不是 `protect` 選項。

## 本節內容

| 頁面 | 內容 |
| --- | --- |
| [用法](usage.md) | 命令行保護、檢查與驗證 |
| [圖形界面](gui.md) | 生成相同命令行的 WPF 前端 |
| [支持範圍](support.md) | 已測試族、主機與明確拒絕項 |
| [設計](design.md) | 工作區佈局、編碼與運行時約定 |
| [開發](development.md) | 構建、測試與貢獻 |

## 許可證

命令行、格式編排與託管元數據寫入器為 AGPL-3.0-only。PE 模型、編解碼實現，以及獨立編寫的原生與託管運行時為 MIT。AGPL 元數據寫入器不會嵌入受保護應用程序。Senbei 是隻讀測試參考，不進入普通工作區構建。
