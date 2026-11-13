---
description: "執行期的除錯器、虛擬機器、系統完整性、注入模組與執行緒、A11/A15 宿主及反掛鉤檢查。"
icon: user-shield
---

# 環境檢查與反分析機制

CrackProof 的啟動檢查橫跨第一階段（展開酬載之前）、`C` / `B` / `A` 序列器各輪掃描，以及分頁保護啟用後選用的 `E` 系列檢查：

{% tabs %}
{% tab title="除錯器" %}
* **`410`（使用者模式反除錯）：** 檢查 `IsDebuggerPresent`（動態擷取確認商用版 `410` 內部不含 SEH 子階段；設定陷阱旗標 `TF` 的 `#DB` SEH 陷阱則是獨立穿插在第 5 階段載入器程式碼中）。
* **`520` 與 `52F`：** 查詢 `NtQueryInformationProcess` 除錯資訊類別（`520`）以及核心除錯器狀態（`52F`）。
* **`BE0`：** 檢查舊版 SoftICE / Syser 驅動程式裝置名稱。
* **計時探測與 `#DB` SEH 陷阱：** 第 5 階段穿插了 `in eax, dx` 計時讀取與 `pushfq; or [rsp], 0x100; popfq` 單步陷阱，正常執行時會由 SEH 處理常式跳過後方的混淆花指令（詳見[分頁保護與載入器程式碼](page-protection.md)）。
{% endtab %}

{% tab title="虛擬機器" %}
* **`540`（VMware 後門埠）：** 對 `0x5658` I/O 埠執行 `in eax, dx` 探測；在實體機與非 VMware 虛擬化環境上會觸發 `#GP` 例外，在 VMware 下則會回傳特徵數值。
* **`A09`（硬體登錄檔前綴檢查）：** 檢查 `HKLM\Hardware\Description\System\SystemBiosVersion`、`HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation\SystemProductName` 與 `HKLM\Hardware\Description\System\BIOS\SystemProductName` 的字串前綴是否符合 `Virtual`、`VMware`、`Bochs`、`VBOX`、`VRTUAL`、`Microsoft Hyper-V` 或 `Parallels`（部分組建亦會在此檢查 CPU 虛擬化功能位元）。
{% endtab %}

{% tab title="系統完整性" %}
* **`C00` 與 `B00`：** 將系統實際組建號（`0x01A00000 + build`）與設定的 Windows 10 以上最低組建門檻比對（`C00`，可識破單純壓低 PEB 回報版號的版本偽造手法），並檢查作業系統相容性（`B00`）。
* **`C01`：** 拒絕在啟用 `testsigning` 或 `disableintegritychecks` 的系統上啟動。
* **`BD0`：** 若偵測到 `C:\Windows\msc.log.log` 存在即中止執行。
* **`E55` 與 `E91`：** 在 `1B40` 家族組建上，探測常見分析工具驅動程式（如 OpenArk 與 Cheat Engine）建立的符號連結裝置。
{% endtab %}

{% tab title="行程與宿主 (A11 / A15)" %}
* **`A03`：** 限制允許的父行程名稱（通常僅允許 `explorer.exe` 或 `cmd.exe`）。
* **`A0F`：** 掃描已載入模組（包含 `AppInit_DLLs`、`user32.dll`、`apphelp.dll` 與 `ShimEng.dll`），且部分宿主組建也會拒絕應用程式資料夾內出現非預期的 DLL。
* **`A07` 與 `A01`：** 終止非預期的外來執行緒（`A07`），若仍有外來執行緒殘留則直接中止啟動（`A01`）。
* **`A11`（DLL 宿主驗證）：** 檢查目前行程中映射的宿主 EXE，只要具備名為 `peC` 的區段，或含有精確大小寫 `KeRnEl32.dLl` 的匯入描述元即視為合法（Windows 解析 DLL 名稱時不分大小寫，這組大小寫混排字串專門用來標記 CrackProof 宿主）。另有第二種 `A11` 變體會額外檢查一組旗標參數。
* **`A15`（DLL 序列器標記）：** 本身不含檢查邏輯；在受保護 DLL 的序列器流程中，一旦 `A09` / `A11` 通過，便會在 `5D0` 之後發出此標記。宿主 EXE 絕不會記錄 `A15`（該位置改為記錄 `552` / `570`）。
{% endtab %}

{% tab title="反掛鉤" %}
* **`A08` 與 `A04`：** 從 `System32` 映射磁碟上乾淨的 `ntdll.dll` 與 `kernel32.dll`，複製原始 `.text` 位元組以繞過使用者模式的 inline hook；若磁碟上的系統 DLL 本身已遭修改，`A04` 還會直接中止啟動。
{% endtab %}
{% endtabs %}
