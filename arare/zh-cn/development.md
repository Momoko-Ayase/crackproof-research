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
$env:ARARE_MANAGED_TOOLS = (Resolve-Path target/managed-tools).Path
```

开发运行时，`ARARE_MANAGED_TOOLS` 必须是包含 `Arare.ManagedHost.dll`、`Arare.ManagedHost.runtimeconfig.json` 与 `Arare.Bootstrap.dll` 的绝对目录。分发包也可把这三个文件放入 `arare.exe` 旁的 `managed/` 目录。工具发现使用这些显式位置。

托管写入器没有 NuGet 依赖。构建后可创建本地二进制包：

```powershell
& tools/package.ps1 -Architecture x64 -IncludeGui
```

CI 会上传同样的 `arare-windows-x64` 与 `arare-windows-x86` 包。

运行打包后的图形界面需要对应架构的 .NET 10 Desktop Runtime。托管打包需要 .NET 10 运行时；仅使用原生命令行不需要。

## 测试

普通工作区构建不会解析 Senbei。它们编译独立的运行时产物，并使用源码生成的夹具：

```powershell
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --workspace --target i686-pc-windows-msvc
```

把 `SENBEI_SOURCE` 设为未改动的 Senbei 源码检出所在的绝对路径，然后使用 oracle 运行脚本：

完整 oracle 执行还需要选定的 32 位 Mono 运行时。在启动运行脚本前，把 `ARARE_MONO_X86` 设为已存在的运行时可执行文件的绝对路径。运行 Mono 案例时才检查此前提；未选择或选择无效会使该案例失败，不会静默跳过。

```powershell
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release --target i686-pc-windows-msvc
```

运行脚本解析选定源码；如果尚未设置 `ARARE_MANAGED_TOOLS`，则在调用 Cargo 前补充该变量。两个 oracle 目标必须依次运行，因为测试工具共享生成的产物位置。更改运行时 C 或 C# 之后重建托管工具。

托管解析器与工具发现的专项检查：

```powershell
python verification/managed/parser_tests.py
cargo test -p arare-engine --lib managed::tool_discovery_tests
```

解析器检查需要 .NET 10 SDK/参考包，并把生成的产物写到 `target/managed-parser-tests/`。在从源码目录启动托管执行或其 Cargo 测试前，应提供 `ARARE_MANAGED_TOOLS`。仅构建或保护原生文件不需要这些文件。

托管夹具编译会在配置的 `ARARE_DOTNET` 安装中选择最新且完整的正式版 .NET 10 SDK，按版本数字排序，并检查 Roslyn 是否存在。如果该安装中没有合适的编译器，会报告前提条件错误。

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

现行约定在 `docs/design/`。注明日期的评审与实现计划在 `docs/notes/`。面向操作者的文档就是本 GitBook 栏目。
