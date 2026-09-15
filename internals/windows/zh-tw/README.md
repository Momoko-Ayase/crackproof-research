---
description: CrackProof 所保護 Windows PE 文件的內部結構與運行時行為。
---

# CrackProof for Windows 內部機制

CrackProof for Windows 保護 PE32 與 PE32+ 可執行文件和 DLL。受保護文件保留足以加載自舉映像的 PE 外層結構，而原始節、加載器階段、選定的數據目錄、名稱和代碼頁則以變換後的形式保存。運行時會在控制權轉交給原程序前重建映像。

目前觀察到的佈局包括原生與託管映像、舊版基於標記的容器、必須按結構識別的新版佈局，以及將受保護載荷放在伴生文件中的 stub 可執行文件。

## 約定

* 除非另有說明，所有偏移均為自文件起始的十六進制字節偏移。`u32@X` 表示偏移 X 處的小端 32 位值。
* **RVA**（相對虛擬地址）按 PE 的通常含義使用。加載器在按 RVA 佈局的內存映像上工作；在磁盤上，同一偏移也被用作解包後映像緩衝區內的文件偏移。
* 整數運算為固定寬度（32 位或 8 位）迴繞運算，與算法來源的 x86 環境一致。Python 參考代碼中顯式施加掩碼。
* 諸如 `info[3]` 的名稱指從加密文件頭派生的 8-dword 表中的條目（見[受保護文件結構](file-structure/file-format.md)）。

## 內容索引

| 範圍              | 起點                                                |
| --------------- | ------------------------------------------------- |
| 磁盤佈局與構建識別       | [受保護文件結構](file-structure/file-format.md)          |
| 密碼、壓縮與校驗和       | [數據變換](data-transforms/data-transforms.md)        |
| 加載器階段與節恢復       | [加載與節恢復](loading-and-pe-repair/loading/)          |
| 頭、目錄、導入與 CLR 數據 | [PE 重建](loading-and-pe-repair/pe-reconstruction/) |
| 啟動檢查、頁保護與內核組件   | [運行時行為](runtime/runtime.md)                       |
| 分析流程、侷限與常量      | [分析筆記](analysis/analysis.md)                      |

Windows 數據變換頁面對應的測試代碼發佈在[驗證與參考](https://app.gitbook.com/s/2p7kzW649ZlKfmpYdJ87/)中。Huffman/LZ 記號語言與緩衝區內 AES 調度表也出現在 [Android 原生庫格式](https://app.gitbook.com/s/HezwIJwx0lhm5CUG7g8R/)中。
