---
description: "Arare 工作区的构建、测试与贡献流程。"
---

# 开发

## 构建

安装 Rust 1.98.1 或更新版本、面向 x86/x64 的 Visual Studio C++ 工具（含 MASM），以及 Windows SDK。开发使用 MSVC 14.51 与 SDK 10.0.26100。

```powershell
rustup target add i686-pc-windows-msvc
cargo build --release -p arare-cli
```

构建期间会从源码编译两种原生加载器架构。托管打包另外需要 .NET 10 SDK/参考包与 .NET Framework 4 参考程序集：

```powershell
& tools/managed/build.ps1
```

托管写入器没有 NuGet 依赖。构建后可创建本地二进制包：

```powershell
& tools/package.ps1 -Architecture x64
```

## 测试

普通工作区构建不会解析 Senbei。它们编译独立的运行时产物，并使用源码生成的夹具：

```powershell
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --workspace --target i686-pc-windows-msvc
```

把未改动的 `senbei/` 作为 `arare/` 的同级目录，供 oracle crate 使用：

```powershell
cargo test --manifest-path verification/senbei-oracle/Cargo.toml --release
cargo test --manifest-path verification/senbei-oracle/Cargo.toml --release --target i686-pc-windows-msvc
```

两个 oracle 目标必须依次运行。它们的测试工具共享生成的产物位置。更改运行时 C 或 C# 之后重建托管工具。

图形界面冒烟测试：

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui.SmokeTests -c Release --no-build
```

私有解码器往返成功并不足够。格式集成必须通过未改动的 Senbei，运行时声明需要真实执行或 DLL 加载。不得为掩盖差异而从比较中排除整节。

## 约定

- 主机工具为 AGPL-3.0-only。`arare-codec`、`arare-pe` 与独立编写的嵌入运行时为 MIT。不要把 AGPL 实现代码引入嵌入运行时。
- 把 Senbei 当作参考。不要把商用供体可执行文件、抽出的 stub、不透明配置或受保护应用程序导入仓库。
- 公开测试使用生成的夹具。仓库外的现有样本目录由用户自行管理。
- PE 文件偏移与 RVA 不同。读取、复制、分配或写入前须同时校验两者。
- 当前实现不包括 Android 与 IL2CPP 元数据混淆。
- 不要在提交中加入署名尾注。

现行约定在 `docs/design/`。操作页面在 `docs/usage.md`、`docs/support.md`、`docs/format.md` 与 `docs/verification.md`。注明日期的评审与实现计划在 `docs/notes/`。
