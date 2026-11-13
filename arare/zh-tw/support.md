---
description: "支援的 PE 與 CLR 輸入矩陣、封裝階段拒絕條件、結構上限與執行期載入規則。"
icon: circle-check
---

# 支援範圍

Arare 以 Windows 10 與 Windows 11 為目標平台，並已於 Windows 11 組建 26100 上透過原始碼建置的 x86/WOW64 與 x64 原生及 Managed 程式完成執行驗證（尚未單獨執行 Windows 10 測試）。Managed 執行環境已於 .NET Framework 4.8（x86/x64）、CoreCLR 10.0.12（x64）與 Mono 6.13（x86）上驗證通過。

## 支援的輸入矩陣

| 輸入類型 | 內嵌儲存設定檔 | 附屬檔（`._`）設定檔 |
| --- | --- | --- |
| 原生 x86 EXE 或 DLL | `pe32` | `pe32` |
| 原生 x64 EXE 或 DLL | `pe64-classic`, `pe64-modern` | `pe64-classic`（DLL 須具備非零進入點）, `pe64-modern` |
| 原生 x64 DLL（專用版面） | `legacy-dll` | 不支援 |
| 純 IL 的 x86 或 AnyCPU DLL | `pe32` | `pe32` |
| 可辨識為純 IL 的 x86 或 AnyCPU C# EXE | `pe32` | `pe32` |
| 純 IL 的 x64 DLL | `legacy-dll`, `pe64-classic`, `pe64-modern` | `pe64-classic`, `pe64-modern` |
| 純 IL 的 x64 EXE | `pe64-classic`, `pe64-modern` | `pe64-classic`, `pe64-modern` |
| `COR20` `ILONLY` 旗標清除的純 IL DLL | 與同位元數的純 IL DLL 相同 | 與同位元數的純 IL DLL 相同 |

原生 IL2CPP 二進位檔（`GameAssembly.dll` 與宿主 EXE）可直接視同一般原生 PE 進行封裝；獨立的 `global-metadata.dat` 混淆不在 Arare 的支援範圍內。

## 封裝階段拒絕條件

輸入檔若符合下列任一情況，`arare protect` 將直接拒絕處理：

### 原生與共用 PE 限制

* **進入點為零的 classic 附屬 DLL：** `AddressOfEntryPoint` 為零的 `pe64-classic` 附屬 DLL（無進入點的 DLL 請改用內嵌儲存或 `pe64-modern`）。
* **附屬檔 TLS 範圍重疊：** TLS 項目範圍與載入器保留實體資料區重疊的 x64 附屬檔輸入。
* **頁面加密的對齊與權限要求：** 啟用頁面加密時，含有可寫入且可執行（`RWX`）區段、`SectionAlignment < 0x1000`，或可執行區段之 `VirtualAddress` 未對齊 `0x1000` 的輸入檔。
* **僅含繫結匯入（bound-only imports）：** `OriginalFirstThunk == 0` 且映像內無 hint/name RVA 或 VA 的原生匯入描述元。
* **PE32 EXE 匯入正規化限制：** 需要改寫區段名稱或權限才能讓靜態解包工具還原匯入表的原生 PE32 EXE。
* **啟用 XFG 的程式碼匯出：** 同時具備程式碼匯出與 `IMAGE_GUARD_XFG_ENABLED` 旗標的原生模組。
* **映像大小與標頭上限：** 總映像大小（含新增的 Arare 區段）超過 `1 GiB`、區段數量超過 `96` 個，或區段標頭總長超過 `0x1000` 位元組（`pe64-*` / `legacy-dll`）或 `0x400` 位元組（`pe32`）。

### Managed 組件限制

* 真正的 C++/CLI 混合模式程式碼、原生 CLR 進入點或 vtable 修正表（vtable fixups）、ReadyToRun/AOT 映像，或非 IL 方法主體。
* 強式名稱（strong-named）或延遲簽署組件、多模組組件、連結／匯出模組表、內嵌式 Portable PDB，或編號 `>= 45` 的 CLI 中繼資料表（例如 `/debug:embedded`）。
* 清除 `ILONLY` 的 x86 Managed EXE、設定 `32BITREQUIRED` 或 `32BITPREFERRED` 的 PE32+ Managed 輸入、RVA 頁面 `[0x1000, 0x2000)` 已被佔用的 `pe64-modern` 零匯入組件，或匯入目錄非零但第一筆描述元為空的 `pe64-modern` Managed 輸入。
* 原生匯出、原生例外／堆疊展開（unwind）或 TLS 目錄、載入組態表（load-config）、延遲載入匯入、`VirtualSize > SizeOfRawData` 的區段、編輯後繼續（Edit-and-Continue）或指標中繼資料表、CLI `vararg` 方法，或位於保留命名空間 `Arare.Managed` 內的型別。
* 中繼資料擴增超過 `524,288` 筆泛型填充 `TypeDef` 列，或簽章回傳型別超過 `128` 層巢狀深度或 `65,536` 個型別元素。

## 版面配置與執行期載入注意事項

* **位於可執行區段內的資料匯出：** PE 匯出表並未區分程式碼與資料項目，因此指向可執行區段的非轉送（non-forwarder）匯出項目會被包上一層程式碼匯出保護跳板（thunk），而不會在封裝階段遭到拒絕。請將匯出的資料符號置於不可執行的資料區段中。
* **位元組陣列載入與磁碟載入：** 採用附屬檔模式封裝的 Managed 組件必須從磁碟檔案載入，不支援 `Assembly.Load(byte[])`。清除 `ILONLY` 的純 IL DLL 則遵循標準 CLR 混合模式載入規則（在 .NET Framework 與 CoreCLR 上須由相同位元數的行程從磁碟載入；Mono 則同時支援磁碟與位元組陣列載入）。
