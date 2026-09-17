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
```

託管寫入器沒有 NuGet 依賴。構建後可創建本地二進制包：

```powershell
& tools/package.ps1 -Architecture x64
```

## 測試

普通工作區構建不會解析 Senbei。它們編譯獨立的運行時產物，並使用源碼生成的夾具：

```powershell
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --workspace --target i686-pc-windows-msvc
```

把未改動的 `senbei/` 作為 `arare/` 的同級目錄，供 oracle crate 使用：

```powershell
cargo test --manifest-path verification/senbei-oracle/Cargo.toml --release
cargo test --manifest-path verification/senbei-oracle/Cargo.toml --release --target i686-pc-windows-msvc
```

兩個 oracle 目標必須依次運行。它們的測試工具共享生成的產物位置。更改運行時 C 或 C# 之後重建託管工具。

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

現行約定在 `docs/design/`。操作頁面在 `docs/usage.md`、`docs/support.md`、`docs/format.md` 與 `docs/verification.md`。註明日期的評審與實現計劃在 `docs/notes/`。
