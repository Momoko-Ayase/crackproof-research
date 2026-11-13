---
description: "CLI 的 protect、inspect 與 verify：版面設定檔、環境檢查、頁面加密與除錯記錄。"
icon: terminal
---

# 使用說明

建置 `arare-cli` 會產出 `target/release/arare.exe`，無須準備 Senbei 原始碼。對 Managed 組件進行封裝時，另需安裝 .NET 10 Runtime，並將三個 Managed 工具檔（`Arare.ManagedHost.dll`、`Arare.ManagedHost.runtimeconfig.json`、`Arare.Bootstrap.dll`）放入 `arare.exe` 旁的 `managed/` 目錄，或透過 `ARARE_MANAGED_TOOLS` 指定路徑（請參閱 [開發指南](development.md)）。批次 GUI 操作請參閱 [GUI 介面](gui.md)。

```text
arare protect INPUT -o|--output OUTPUT --profile PROFILE
    [--seed 64_HEX_DIGITS] [--no-compression]
    [--storage embedded|companion] [--check NAME=on|off]...
    [--page-encrypt on|off] [--scribble on|off]
    [--errlog on|off] [--antidebug-av on|off]
    [--force] [--json]

arare inspect INPUT [--json]

arare verify INPUT --profile PROFILE [--companion PATH] [--json]
```

## 版面設定檔與儲存模式

| 設定檔 | 目標版面家族 |
| --- | --- |
| `pe32` | PE32 x86 原生映像，以及支援的 x86／AnyCPU Managed 組件 |
| `pe64-classic` | 傳統含標記 EXE 風格的 PE32+ x64 EXE 與 DLL |
| `pe64-modern` | 無標記 EXE 風格的 PE32+ x64 EXE 與 DLL |
| `legacy-dll` | 舊式專用 PE32+ x64 DLL 版面配置（僅支援內嵌儲存） |

設定檔名稱對應的是結構版面家族，而非商業產品版本；輸入限制請參閱 [支援範圍](support.md)。

* **附屬檔儲存（`--storage companion`）：** 同時寫出 `OUTPUT`（4 KiB 標頭／覆寫 stub）與 `<OUTPUT>._`（加密酬載，透過 `0x1000..0x1020` 的 32 位元組標頭配對）。請將兩個檔案放在同一個資料夾內。
* **種子與壓縮：** 省略 `--seed` 時會從 Windows CSPRNG 抽取 32 個隨機位元組並印出十六進位種子。`--no-compression` 會在保留載入器各階段編碼的前提下，以未壓縮形式儲存應用程式區段區塊。
* **靜態驗證（`verify`）：** 使用 Arare 獨立的原生解碼器解碼受保護檔案，不會執行目標程式。省略 `--companion` 時，只要 `<INPUT>._` 的 32 位元組標頭相符，`verify` 便會自動配對。

## 環境檢查與失敗處置

受保護模組會在三個啟動階段執行可開關的環境檢查（第 1 階段位於載入檔案內容前，第 2 階段位於載入後，第 3 階段位於啟用頁面保護後）。可重複傳入 `--check NAME=on|off` 覆寫預設值：

| 模組類型 | 預設啟用的檢查項目 |
| --- | --- |
| 原生 EXE | `antidebug`, `crc-loader`, `debug-port`, `os-version`, `boot-options`, `vm-registry`, `injected-dll`, `injected-thread`, `clean-code` |
| 原生 DLL | `crc-loader`, `vm-registry`, `host-process` |
| Managed EXE | `crc-loader`, `vm-registry` |
| Managed DLL | `crc-loader`, `vm-registry`, `host-process` |

由於兩種 DLL 的 `host-process` 預設皆為 `on`，若要在未受保護的宿主行程中載入受保護 DLL，必須加上 `--check host-process=off`。`vm-backdoor`、`parent-process` 與 `hyperv-guest` 在所有模組類型中預設皆為 `off`。

| CLI 檢查名稱 | 階段碼 | 檢查行為 |
| --- | --- | --- |
| `antidebug` | `410` | 7 個子階段：`IsDebuggerPresent`、`PEB.BeingDebugged`、`PEB.NtGlobalFlag & 0x70`、硬體除錯暫存器 `DR0`..`DR3` / `DR7 & 0xFF`（`GetThreadContext`），以及 `NtQueryInformationProcess`（`ProcessDebugPort`、`ProcessDebugFlags == 0`、`ProcessDebugObjectHandle`） |
| `crc-loader` | `510` | 載入器程式碼 CRC-32 自我檢查 |
| `debug-port` | `520` | 核心除錯連接埠查詢 |
| `kernel-debugger` | `52F` | `KdDebuggerEnabled`／系統核心除錯器檢查 |
| `vm-backdoor` | `540` | VMware `0x5658` I/O 連接埠探測（忽略通用 CPUID hypervisor 位元；允許 Hyper-V/VBS） |
| `hyperv-guest` | `541` | Arare 專屬的 Hyper-V 客體分割區權限檢查（`Hv#1` CPUID） |
| `parent-process` | `A03` | 拒絕非 `explorer.exe` 或 `cmd.exe` 的父行程 |
| `os-version` | `C00` | 要求 Windows 10 組建 `10240` 或更新版本 |
| `boot-options` | `C01` | 拒絕測試簽章（test-signing）與除錯開機旗標 |
| `msc-log` | `BD0` | 若存在 `C:\Windows\msc.log.log` 則拒絕啟動 |
| `os-compat` | `B00` | 作業系統相容性檢查 |
| `vm-registry` | `A09` | 系統硬體／BIOS 虛擬機器登錄檔標記（當 `Hv#1` 識別為 Hyper-V/VBS 時，允許通用的 `Virtual` / `VRTUAL` / `Microsoft Hyper-V`） |
| `injected-dll` | `A0F` | 在進入 OEP 前掃描已載入模組 |
| `injected-thread` | `A07` / `A01` | 偵測非預期的外部注入執行緒 |
| `host-process` | `A11` | 要求相容的 Arare EXE 宿主行程（含 `.arldr` 或 `.armclr` 標記） |
| `host-stamp` | `A11` | 當 `host-process=on` 時，選用的協作式執行階段環境戳記檢查 |
| `clean-code` | `A08` | 透過未受竄改的系統 DLL 程式碼位元組執行載入器呼叫 |
| `disk-integrity` | `A04` | 即使同時指定也會取代 `clean-code`；額外比對記憶體中映射的系統 DLL 與磁碟上的系統映像檔 |
| `legacy-debugger` | `BE0` | 舊式除錯器裝置探測 |
| `openark-device` | `E55` | 啟用頁面保護後的 OpenArk 驅動程式裝置檢查 |
| `cheat-engine-device` | `E91` | 啟用頁面保護後的 Cheat Engine 驅動程式裝置檢查 |

{% hint style="warning" %}
**除非有明確需求，否則不建議啟用 `hyperv-guest`。** `--check hyperv-guest=on` 會拒絕透過 `Hv#1` CPUID 分割區權限識別出的客體 VM，同時允許根分割區／主機端 VBS 環境。由於 hypervisor CPUID 資訊可能遭到遮罩或偽造，請將 `hyperv-guest` 視為執行環境限制，而非防竄改機制。
{% endhint %}

**失敗處置（`--antidebug-av`）：** `--antidebug-av` 在 EXE 上預設為 `on`，在 DLL 上預設為 `off`（原生模組記錄檔中顯示為 `-AV=ON` / `-AV=OFF`）。當啟用 `--antidebug-av=on` 的原生模組檢查未通過時，執行階段會關閉記錄檔、呼叫 `RaiseException(0xC0000005)`（`EXCEPTION_ACCESS_VIOLATION`），並在呼叫 `TerminateProcess(0xE0A00000 | substage)` 前寫入空指標位址，使附加的除錯器立即中斷。設定 `--antidebug-av=off` 的原生模組與 Managed 模組則會直接呼叫 `TerminateProcess`。

## 頁面加密

`--page-encrypt` 在 EXE 上預設為 `on`，在 DLL 上預設為 `off`。區段重建完成後，執行階段會原地重新加密可執行的應用程式頁面，將權限設為 `PAGE_NOACCESS`，並 hook `ntdll!KiUserExceptionDispatcher`，在頁面首次因執行而觸發存取違規例外時即時解密。啟用頁面加密時，若輸入檔含有可寫入且可執行（`RWX`）的區段，或區段對齊小於 `0x1000`，封裝階段即會拒絕。

`--scribble=on`（預設為 `off`，須搭配 `--page-encrypt=on`）會在各次頁面存取例外之間遮罩已解密常駐頁面的特定位元組。

## 除錯記錄與 `ErrLog-Pec`

`protect --json`（以及標準主控台輸出）會回報該模組專屬的 12 位十六進位字元 `log_folder`。只要 `%TEMP%\<log_folder>` 資料夾存在且建立時間未滿 48 小時，模組便會寫入執行階段狀態記錄檔（EXE 為 `HHMMSSmmmE-...`，DLL 為 `HHMMSSmmmD-...`），並以 `AAA-BBB-CCC` 結束摘要收尾。

{% hint style="info" %}
**DLL 記錄閘門繼承規則。** 當受保護的 DLL 載入至受保護的 Arare EXE 行程內時，即使兩者使用不同種子，甚至設為 `host-process=off`，一律由該 EXE 的記錄狀態決定 DLL 是否寫入記錄。若 EXE 的 `%TEMP%` 資料夾不存在或已超過 48 小時，即使 DLL 自身的備援 `log_folder` 存在，DLL 仍不會輸出記錄。
{% endhint %}

`--errlog=on`（預設為 `off`）會將結束診斷封包傳送至 `\\.\mailslot\ErrLog-Pec<suffix>`（其中 `<suffix>` 為 `((key + 1) * 0x3039) % 0x8003` 算出的四位十六進位數字），內容包含時間戳記、`AAA-BBB-CCC` 代碼及模組／OS 資訊，不受 `%TEMP%` 資料夾閘門限制。

## 輸出寫入與 JSON 報告

所有輸出皆先在記憶體中完整編碼，接著寫入暫存檔、強制寫入磁碟（flush）並以原子重新命名完成輸出（覆寫既有檔案須加上 `--force`）。若輸出路徑為輸入檔的符號連結或正規化路徑別名，程式會直接拒絕；取代獨立的硬連結（hard link）項目則會保留原始輸入檔位元組不受影響。

<details>
<summary>JSON 輸出欄位（protect、inspect、verify）</summary>

* **`protect --json`：** `output`, `profile`, `storage`, `architecture`, `module`, `input_size`, `output_size`, `seed`, `normalizations`, `log_folder`, `companion`, `companion_size`。
* **`inspect --json`：** `architecture`, `module`, `entry_point`, `image_base`, `image_size`, `file_size`, `sections`（`name`, `rva`, `virtual_size`, `raw_offset`, `raw_size`, `characteristics`）。
* **`verify --json`：** `valid`, `profile`, `companion`, `image_size`, `recovered_file_size`, `entry_point`。
</details>
