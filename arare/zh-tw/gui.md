---
description: "根據作業列表生成 arare protect 命令行的 WPF 前端。"
---

# 圖形界面

Arare 命令行的 WPF 前端。它根據作業列表生成 `arare protect` 調用，運行前顯示確切命令，並按順序執行作業，可選在保護後驗證。

需要 .NET 10 SDK，與託管工具使用的 SDK 相同。

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui
```

把 `Arare.Gui.exe` 放在 `arare.exe` 旁邊。圖形界面先在自身旁邊查找 `arare.exe`，再查 `PATH`。探測失敗時可在狀態欄選擇其他位置。

位置參數會預先加入文件與文件夾：

```powershell
Arare.Gui.exe app.exe game_folder\
```

文件夾掃描規則與文件夾選擇器相同：根目錄，加上最多三層深的 `Managed` 或 `Plugins` 目錄。

## 行為

- 每一行作業擁有自己的保護配置。建議配置來自 PE：x86 對應 `pe32`，x64 對應 `pe64-modern`，AnyCPU 託管映像對應 `pe32`。`legacy-dll` 只對 64 位 DLL 有效。
- 輸出默認寫到各輸入旁的 `.\arare-protected\`，或寫到選定的輸出文件夾並保留文件名。
- 環境檢查、頁加密與 scribble 跟隨命令行按模塊類型的默認值，包括 `disk-integrity` 取代 `clean-code` 的規則。複選框顯示所選行的解析狀態；覆蓋某選項會做標記並提供復位。
- 命令預覽始終對應當下將要運行的內容。它使用虛擬化，因此含數千個文件的文件夾仍能保持響應。
- 保護按順序運行作業，可在文件之間取消。啟用“保護後檢查編碼”時，每個輸出用 `arare verify` 檢查。該解碼器檢查不啟動程序。
- 設置保存在可執行文件旁的 `Arare.Gui.settings.json`。作業列表不會持久化。

## 測試

```powershell
dotnet run --project gui/Arare.Gui.SmokeTests
```

覆蓋 PE 分類、命令構造、覆蓋/默認模型、預覽生成、校驗、針對假後端的保護/驗證流程、運行中關閉握手、文件夾掃描規則與設置持久化。

許可證為 AGPL-3.0-only，與命令行一致。
