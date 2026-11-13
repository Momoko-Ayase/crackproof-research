---
description: "建置原生與 Managed 工具鏈、執行測試與 Senbei 1.3.1 對照驗證並打包發行版。"
icon: hammer
---

# 開發指南

## 建置專案

前置需求：Rust `1.98.1` 或更新版本、包含 MASM（`ml` / `ml64`）的 Visual Studio C++ x86/x64 建置工具，以及 Windows 10/11 SDK（已於 MSVC `14.51` 與 SDK `10.0.26100` 測試通過）。Managed 封裝與 WPF GUI 另需安裝 .NET 10 SDK 與 .NET Framework 4 參考組件。

{% stepper %}
{% step %}
### 建置原生 CLI 與內嵌載入器

`cargo build` 會從原始碼同時編譯 x86 與 x64 的 C/ASM 執行階段載入器：

```powershell
rustup target add i686-pc-windows-msvc
cargo build --release -p arare-cli
```
{% endstep %}

{% step %}
### 建置 Managed 中繼資料工具（處理 CLR 輸入必備）

`tools/managed/build.ps1` 無任何 NuGet 相依套件（若 `dotnet.exe` 不在預設路徑，可傳入 `-Dotnet <path>`），執行後會產出 `Arare.ManagedHost.dll`、`Arare.ManagedHost.runtimeconfig.json` 與 `Arare.Bootstrap.dll`：

```powershell
& tools/managed/build.ps1
$env:ARARE_MANAGED_TOOLS = (Resolve-Path target/managed-tools).Path
```

每當 `runtime/` 或 `tools/managed/` 底下的檔案變更時，請重新執行 `tools/managed/build.ps1`。執行期間，除非透過 `ARARE_DOTNET` 指定 `dotnet.exe` 的絕對路徑，否則 `arare` 與 Python 測試腳本預設會在 `C:/Program Files/dotnet/dotnet.exe` 尋找 `dotnet.exe`。
{% endstep %}

{% step %}
### 打包發行壓縮檔（選用）

組裝獨立的 `arare-windows-x64` 或 `arare-windows-x86` 發行目錄（包含 `managed/`，並可選擇一併納入 `Arare.Gui.exe`）：

```powershell
& tools/package.ps1 -Architecture x64 -IncludeGui
```
{% endstep %}
{% endstepper %}

## 測試驗證

{% tabs %}
{% tab title="Workspace 檢查" %}
標準 workspace 測試使用動態產生的測試 fixture，無須準備 Senbei 原始碼：

```powershell
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --workspace --target i686-pc-windows-msvc
```
{% endtab %}

{% tab title="Senbei 1.3.1 對照驗證" %}
`verification/run_oracle.py` 會以**未修改的 Senbei `1.3.1` 原始碼目錄**（限定 `version = "=1.3.1"`；若將 `SENBEI_SOURCE` 指向較新版本的 Senbei 會被版本檢查拒絕）驗證每一種封裝設定檔，並實際執行原始檔、受保護檔與解包還原檔。執行前請先將 `ARARE_MONO_X86` 設為 32 位元 `mono.exe` 的絕對路徑；由於 x64 與 x86 測試共用產物路徑，請依序執行兩個目標架構：

```powershell
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release --target i686-pc-windows-msvc
```
{% endtab %}

{% tab title="Managed 與 GUI 測試套件" %}
執行 ECMA-335 解析器／改寫器測試、Managed 工具探索單元測試，以及 WPF 冒煙測試套件：

```powershell
python verification/managed/parser_tests.py
cargo test -p arare-engine --lib managed::tool_discovery_tests
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui.SmokeTests -c Release --no-build
```
{% endtab %}
{% endtabs %}

## 開發規範

* 確保 `arare-pe`、`arare-codec` 與所有內嵌執行階段程式碼（`arare-runtime`、`runtime/`）維持純淨的 `MIT` 授權；嚴禁將 `AGPL-3.0-only` 程式碼移入內嵌執行階段。
* 嚴禁將商業樣本檔案、擷取出的外部 stub 或真實受保護樣本匯入儲存庫；所有測試一律使用動態產生的 fixture。
* 將檔案偏移與 RVA 視為不同的座標空間，並在切片讀取或寫入前同時驗證兩者的邊界。
* 任何格式變更皆須同時通過未修改版 Senbei 的靜態還原與真實作業系統行程／DLL 執行驗證，不得僅依賴內建解碼器的往返測試或排除特定區段。
* 架構規格置於 `docs/design/`，附日期的研究證據與計畫置於 `docs/notes/`，使用者說明文件則維護於本 GitBook 專區。提交 commit 時請勿加上任何署名尾註（attribution trailers）。
