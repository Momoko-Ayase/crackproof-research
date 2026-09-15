---
description: "面向 CrackProof 保護的 Windows PE 與 Android 共享庫的靜態解包器。"
---

# Senbei

Senbei 是面向 CrackProof 保護程序的靜態解包器。指向一個文件、應用包或文件夾，它會在不啟動、也不附加到受保護程序的情況下寫出恢復後的副本。

Senbei 讀取受保護字節，重放保護算法，按結構檢查驗證結果，然後寫出恢復後的映像。驗證失敗的候選結果會被拒絕，絕不會作為靜默損壞的二進制文件發出。

支持的輸入：

* 受保護的 Windows `.exe` 與 `.dll` 文件（64 位與 32 位、原生與託管），包括外置 `.exe._`、`.dll._` 伴生載荷
* 具有受支持方法令牌佈局的 `global-metadata.dat` 文件
* 受保護的 Android `.so` 文件，可為獨立文件，也可位於 `.apk`、`.apks`、`.xapk` 包內

這些輸入所對應的保護格式與運行時行為記錄在 [CrackProof Windows 內部機制](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/) 與 [CrackProof Android SO 內部機制](https://app.gitbook.com/s/HezwIJwx0lhm5CUG7g8R/)。

## 本節內容

| 頁面 | 內容 |
| --- | --- |
| [用法](usage.md) | 命令行工具的運行方式：目標、標誌與退出碼 |
| [設計](design.md) | 工作區與恢復流水線的組織方式 |
| [開發](development.md) | 構建、測試與貢獻 |

## 瀏覽器版

同一引擎也可編譯為 WebAssembly，在瀏覽器中運行。文件在本地處理，不會上傳。瀏覽器版處理單個文件；文件夾掃描與 Android 包編排仍由命令行工具負責。
