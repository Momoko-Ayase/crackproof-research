---
description: "用於建立、預覽與執行批次 arare protect 及 verify 工作的 WPF 桌面前端。"
icon: window-maximize
---

# GUI 介面

`Arare.Gui.exe` 是以 Windows Presentation Foundation（WPF）撰寫的桌面前端，可從工作佇列組合 `arare protect` 命令列、預覽完整的 CLI 呼叫參數，並依序執行保護作業與選用的封裝後解碼驗證。

## 建置與啟動

建置專案需要 .NET 10 SDK；執行打包後的 GUI 則需要對應的 .NET 10 Desktop Runtime。

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui -c Release
```

請將 `Arare.Gui.exe` 放在與 `arare.exe` 相同的資料夾內（或確保 `arare.exe` 位於 `PATH` 中），亦可點選狀態列上的 **Locate…** 指定其他執行檔路徑。啟動時可傳入引數以預先載入檔案與資料夾：

```powershell
Arare.Gui.exe app.exe game_folder\
```

* **資料夾選擇器：** 未勾選子資料夾遞迴時，會掃描所選資料夾及最多三層深的 `Managed` 或 `Plugins` 子目錄；啟用子資料夾遞迴後則會走訪完整目錄樹。
* **命令列位置引數：** 啟動時傳入的資料夾引數一律採用非遞迴掃描規則（根目錄加上最多三層深的 `Managed`/`Plugins`），不受已儲存的子資料夾核取方塊設定影響。

## 工作佇列、逐列覆寫與驗證

* **逐列設定檔建議：** 根據 PE 標頭自動帶入建議設定檔（`x86` -> `pe32`、`x64` -> `pe64-modern`、`AnyCPU` Managed -> `pe32`；`legacy-dll` 僅限 64 位元 DLL 選用）。
* **輸出路徑與衝突檢查：** 預設輸出至各輸入檔旁的 `.\arare-protected\`（或單一指定資料夾）。若出現重複的輸出路徑，或任何輸出檔（含 `._` 附屬檔）會覆寫佇列中的輸入檔，即使已勾選 **Replace existing outputs**，仍會在執行前阻擋。
* **有效選項狀態解析：** 環境檢查、頁面加密、scribble 與 **ErrLog** mailslot 回報（`--errlog`）的核取方塊會即時反映該模組類型的有效預設值（包含 `disk-integrity` 取代 `clean-code` 的規則），標示逐列覆寫項目，並提供單鍵重設。`--antidebug-av` 未在 GUI 中提供開關，一律沿用 CLI 依模組類型決定的預設值（EXE 為 `on`，DLL 為 `off`）。
* **匯出腳本與執行：** **Copy as .ps1** 會匯出明確的 PowerShell 呼叫腳本，負責建立輸出目錄、執行 `arare protect`（及選用的 `arare verify`），並在遇到非零結束代碼時立即停止。**Protect 1 file** / **Protect N files** 會依序執行佇列工作；點選 **Cancel** 會在目前項目處理完成後停止。
* **獨立驗證：** **Verify existing…** 可在不啟動目標程式的前提下，對已受保護的檔案逐一測試候選設定檔執行 `arare verify`；勾選 **Check encoding after protect** 則會在每筆保護工作完成後自動執行 `arare verify`。
* **偏好設定儲存：** 介面偏好設定會寫入執行檔旁的 `Arare.Gui.settings.json`；工作佇列本身僅保留於當次執行階段。

## 冒煙測試

```powershell
dotnet run --project gui/Arare.Gui.SmokeTests -c Release
```

測試套件涵蓋 PE 類型判別、CLI 引數產生、依模組類型的預設值與覆寫解析、`.ps1` 腳本匯出、路徑衝突檢查、搭配模擬後端的保護與驗證狀態轉換、執行期間關閉視窗的確認提示、資料夾掃描深度規則，以及設定檔讀寫。採用 `AGPL-3.0-only` 授權。
