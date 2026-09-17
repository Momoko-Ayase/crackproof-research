---
description: CrackProof 保護格式與運行時行為的獨立技術研究。
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

# CrackProof 研究

CrackProof® 是 HyperTech 開發的一系列商用二進制保護系統。本站記錄通過獨立分析驗證的文件格式、數據變換、加載器與運行時組件。

當前研究範圍包括 Windows PE 文件和 Android 原生庫。兩個平臺使用不同的容器格式與恢復路徑，因此分別編寫內部機制文檔。

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><strong>Windows 內部機制</strong></td><td>受保護 PE 佈局、數據變換、分階段加載、PE 重建與運行時行為。</td><td><a href="https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/">CrackProof for Windows 內部機制</a></td></tr><tr><td><strong>Android SO 內部機制</strong></td><td>受保護 AArch64 ELF 佈局、模塊流、容器解碼、ELF 恢復與 IL2CPP 元數據。</td><td><a href="https://app.gitbook.com/s/HezwIJwx0lhm5CUG7g8R/">CrackProof for Android SO 內部機制</a></td></tr><tr><td><strong>驗證與參考</strong></td><td>文中 Windows 數據變換的可執行測試向量與小型參考實現。</td><td><a href="https://app.gitbook.com/s/2p7kzW649ZlKfmpYdJ87/">驗證與參考</a></td></tr><tr><td><strong>Senbei</strong></td><td>本項目面向受保護 Windows PE 文件與 Android 共享庫的靜態解包器：用法、設計與開發。</td><td><a href="https://app.gitbook.com/s/v6LkixcUwwnaXW5PFCVE/">Senbei</a></td></tr><tr><td><strong>Arare</strong></td><td>本項目面向 Windows PE 的源碼生成保護器：用法、圖形界面、支持範圍、設計與開發。</td><td><a href="https://app.gitbook.com/s/7HowntiXDyzWEvoMUZzH/">Arare</a></td></tr></tbody></table>

## 研究邊界

文檔只描述可觀察的結構與行為。名稱來自二進制、日誌、已有平臺術語，或對字段作用的直白說明。只有經過多個樣本驗證，或能通過內部一致性約束證明的結論，才會寫成格式行為。

文檔不記錄受保護產品名稱、部署專用驅動名和可識別樣本的信息。研究頁面不點名用於驗證結論的實現項目；Senbei 與 Arare 欄目單獨記錄本項目自己的工具。

## 法律聲明

僅可將這些信息用於您擁有或已獲明確授權分析的二進制。各司法轄區的規避限制與許可條款不同。本文檔是獨立研究成果，不包含廠商源代碼或密鑰，與 HyperTech 無隸屬關係，也不授權再分發恢復後的二進制。
