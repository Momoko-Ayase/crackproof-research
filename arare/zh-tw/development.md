---
description: "Arare 工作區的構建、測試與貢獻流程。"
---

# 開發

## 構建

安裝 Rust 1.98.1 或更新版本、面向 x86/x64 的 Visual Studio C++ 工具（含 MASM），以及 Windows SDK。開發使用 MSVC 14.51 與 SDK 10.0.26100。

```powershell
rustup target add i686-pc-windows-msvc
cargo build --release -p arare-cli
```

構建期間會從源碼編譯兩種原生加載器架構。託管打包另外需要 .NET 10 SDK/參考包與 .NET Framework 4 參考程序集：

```powershell
& tools/managed/build.ps1
$env:ARARE_MANAGED_TOOLS = (Resolve-Path target/managed-tools).Path
```

開發運行時，`ARARE_MANAGED_TOOLS` 必須是包含 `Arare.ManagedHost.dll`、`Arare.ManagedHost.runtimeconfig.json` 與 `Arare.Bootstrap.dll` 的絕對目錄。分發包也可把這三個文件放入 `arare.exe` 旁的 `managed/` 目錄。工具發現使用這些顯式位置。

託管寫入器沒有 NuGet 依賴。構建後可創建本地二進制包：

```powershell
& tools/package.ps1 -Architecture x64 -IncludeGui
```

CI 會上傳同樣的 `arare-windows-x64` 與 `arare-windows-x86` 包。

運行打包後的圖形界面需要對應架構的 .NET 10 Desktop Runtime。託管打包需要 .NET 10 運行時；僅使用原生命令行不需要。

## 測試

普通工作區構建不會解析 Senbei。它們編譯獨立的運行時產物，並使用源碼生成的夾具：

```powershell
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --workspace --target i686-pc-windows-msvc
```

把 `SENBEI_SOURCE` 設為未改動的 Senbei 源碼檢出所在的絕對路徑，然後使用 oracle 運行腳本：

完整 oracle 執行還需要選定的 32 位 Mono 運行時。在啟動運行腳本前，把 `ARARE_MONO_X86` 設為已存在的運行時可執行文件的絕對路徑。運行 Mono 案例時才檢查此前提；未選擇或選擇無效會使該案例失敗，不會靜默跳過。

```powershell
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release --target i686-pc-windows-msvc
```

運行腳本解析選定源碼；如果尚未設置 `ARARE_MANAGED_TOOLS`，則在調用 Cargo 前補充該變量。兩個 oracle 目標必須依次運行，因為測試工具共享生成的產物位置。更改運行時 C 或 C# 之後重建託管工具。

託管解析器與工具發現的專項檢查：

```powershell
python verification/managed/parser_tests.py
cargo test -p arare-engine --lib managed::tool_discovery_tests
```

解析器檢查需要 .NET 10 SDK/參考包，並把生成的產物寫到 `target/managed-parser-tests/`。在從源碼目錄啟動託管執行或其 Cargo 測試前，應提供 `ARARE_MANAGED_TOOLS`。僅構建或保護原生文件不需要這些文件。

託管夾具編譯會在配置的 `ARARE_DOTNET` 安裝中選擇最新且完整的正式版 .NET 10 SDK，按版本數字排序，並檢查 Roslyn 是否存在。如果該安裝中沒有合適的編譯器，會報告前提條件錯誤。

圖形界面冒煙測試：

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui.SmokeTests -c Release --no-build
```

私有解碼器往返成功並不足夠。格式集成必須通過未改動的 Senbei，運行時聲明需要真實執行或 DLL 加載。不得為掩蓋差異而從比較中排除整節。

## 約定

- 主機工具為 AGPL-3.0-only。`arare-codec`、`arare-pe` 與獨立編寫的嵌入運行時為 MIT。不要把 AGPL 實現代碼引入嵌入運行時。
- 把 Senbei 當作參考。不要把商用供體可執行文件、抽出的 stub、不透明配置或受保護應用程序導入倉庫。
- 公開測試使用生成的夾具。倉庫外的現有樣本目錄由用戶自行管理。
- PE 文件偏移與 RVA 不同。讀取、複製、分配或寫入前須同時校驗兩者。
- 當前實現不包括 Android 與 IL2CPP 元數據混淆。
- 不要在提交中加入署名尾註。

現行約定在 `docs/design/`。註明日期的評審與實現計劃在 `docs/notes/`。面向操作者的文檔就是本 GitBook 欄目。
