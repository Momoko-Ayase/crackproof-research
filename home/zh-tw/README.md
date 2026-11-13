---
description: "針對 CrackProof 保護格式與執行階段行為的獨立技術研究。"
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

# CrackProof 技術研究

CrackProof® 是 HyperTech 推出的商業二進位保護系統系列。本站記錄經獨立驗證的檔案格式、資料轉換、分階段載入器與執行階段元件細節。

研究範圍涵蓋受 CrackProof for Windows® 保護的 PE 檔案，以及受保護的 Android AArch64 共用程式庫。兩個平台採用不同的容器格式與還原流程，因此分區說明各自的內部機制。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-desktop"></i></td><td><strong>Windows 內部機制</strong></td><td>受保護的 PE 版面配置、加密演算法、分階段載入、PE 重建與執行階段檢查。</td><td><a href="https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/">CrackProof for Windows® 內部機制</a></td></tr><tr><td><i class="fa-mobile-screen-button"></i></td><td><strong>Android SO 內部機制</strong></td><td>受保護的 AArch64 ELF 版面配置、巢狀模組串流、容器解碼、ELF 還原與 IL2CPP 中繼資料。</td><td><a href="https://app.gitbook.com/s/HezwIJwx0lhm5CUG7g8R/">CrackProof for Android SO 內部機制</a></td></tr><tr><td><i class="fa-code"></i></td><td><strong>驗證與參考實作</strong></td><td>對應 Windows 資料轉換的可執行測試向量、Python 參考實作與去識別化除錯記錄。</td><td><a href="https://app.gitbook.com/s/2p7kzW649ZlKfmpYdJ87/">驗證與參考實作</a></td></tr><tr><td><i class="fa-screwdriver-wrench"></i></td><td><strong>Senbei</strong></td><td>支援受保護 Windows PE、Android 共用程式庫與 IL2CPP 中繼資料的靜態解包工具，涵蓋 CLI、桌面版 GUI、架構設計與開發說明。</td><td><a href="https://app.gitbook.com/s/v6LkixcUwwnaXW5PFCVE/">Senbei</a></td></tr><tr><td><i class="fa-shield-halved"></i></td><td><strong>Arare</strong></td><td>從原始碼建置並重現已知結構家族的 Windows PE 保護器，涵蓋 CLI、GUI、支援矩陣、架構設計與開發說明。</td><td><a href="https://app.gitbook.com/s/7HowntiXDyzWEvoMUZzH/">Arare</a></td></tr></tbody></table>

## 研究範圍

文中記載的每項規則皆來自可觀測的二進位結構與執行階段行為。欄位與元件名稱依循二進位檔內建字串、除錯記錄輸出、標準平台規格，或直接描述位元組的實際作用。唯有在多個樣本呈現一致行為，或有內部一致性檢查強制約束時，才會歸納為格式通則。

研究章節全面略去受保護產品名稱、特定部署環境的驅動程式檔名，以及可識別樣本的路徑。Senbei 與 Arare 則於各自的產品專區獨立說明。

{% hint style="warning" %}
**法律聲明。** 本站內容僅供分析您本人擁有或已取得明確授權的二進位檔。各司法管轄區對於規避科技保護措施的法令與授權條款規定不同。本獨立研究不包含任何廠商原始碼或金鑰，與 HyperTech 無任何關聯，亦不授權重新散佈還原後的二進位檔。
{% endhint %}
