---
description: "构建原生与托管工具链，运行工作区测试与 Senbei 1.3.1 基准验证，以及打包发行版。"
icon: hammer
---

# 开发指南

## 编译构建

前置依赖：Rust `1.98.1` 或更高版本、带 MASM（`ml` / `ml64`）的 Visual Studio C++ x86/x64 生成工具，以及 Windows 10/11 SDK（已在 MSVC `14.51` 与 SDK `10.0.26100` 下验证）。托管程序集加壳与 WPF GUI 还需安装 .NET 10 SDK 及 .NET Framework 4 引用程序集。

{% stepper %}
{% step %}
### 编译原生 CLI 与内嵌加载器

`cargo build` 会从源码同时编译 x86 与 x64 的 C/ASM 运行时加载器：

```powershell
rustup target add i686-pc-windows-msvc
cargo build --release -p arare-cli
```
{% endstep %}

{% step %}
### 编译托管元数据工具（处理 CLR 输入必需）

`tools/managed/build.ps1` 无任何外部 NuGet 依赖（若 `dotnet.exe` 不在默认安装位置，可传入 `-Dotnet <path>`），构建后生成 `Arare.ManagedHost.dll`、`Arare.ManagedHost.runtimeconfig.json` 与 `Arare.Bootstrap.dll`：

```powershell
& tools/managed/build.ps1
$env:ARARE_MANAGED_TOOLS = (Resolve-Path target/managed-tools).Path
```

每当修改了 `runtime/` 或 `tools/managed/` 下的文件后，都需重新运行 `tools/managed/build.ps1`。运行时，`arare` 与 Python 测试脚本默认从 `C:/Program Files/dotnet/dotnet.exe` 查找 `dotnet.exe`，也可通过 `ARARE_DOTNET` 指定其绝对路径。
{% endstep %}

{% step %}
### 打包发行压缩包（可选）

打包生成独立的 `arare-windows-x64` 或 `arare-windows-x86` 发行目录（内含 `managed/`，并可选附带 `Arare.Gui.exe`）：

```powershell
& tools/package.ps1 -Architecture x64 -IncludeGui
```
{% endstep %}
{% endstepper %}

## 测试验证

{% tabs %}
{% tab title="工作区常规检查" %}
标准工作区测试全部使用动态生成的测试 fixture，无需检出 Senbei 仓库：

```powershell
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --workspace --target i686-pc-windows-msvc
```
{% endtab %}

{% tab title="Senbei 1.3.1 基准验证" %}
`verification/run_oracle.py` 会将每种加壳配置的输出交给**未修改的 Senbei `1.3.1` 源码树**（固定约束 `version = "=1.3.1"`，若 `SENBEI_SOURCE` 指向更高版本的 Senbei 会被版本检查直接拒绝）验证静态脱壳，并在实机上实际运行原程序、加壳产物和脱壳产物。运行前请将 `ARARE_MONO_X86` 设为 32 位 `mono.exe` 的绝对路径；由于 x64 与 x86 目标共用生成的中间产物路径，请串行执行两套测试：

```powershell
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release --target i686-pc-windows-msvc
```
{% endtab %}

{% tab title="托管与 GUI 测试套件" %}
运行 ECMA-335 解析与重写测试、托管工具路径查找单元测试，以及 WPF 冒烟测试套件：

```powershell
python verification/managed/parser_tests.py
cargo test -p arare-engine --lib managed::tool_discovery_tests
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui.SmokeTests -c Release --no-build
```
{% endtab %}
{% endtabs %}

## 贡献规范

* 保持 `arare-pe`、`arare-codec` 及所有内嵌运行时代码（`arare-runtime`、`runtime/`）仅采用 `MIT` 许可证，严禁将任何 `AGPL-3.0-only` 代码移入内嵌运行时。
* 严禁向仓库引入商业样本二进制、提取出的存根或受保护的真实程序样本；所有测试一律使用自动生成的 fixture。
* 严格区分文件偏移与 RVA 两个坐标空间，切片读写前必须分别完成边界校验。
* 任何格式改动都必须通过未修改版 Senbei 的静态还原与真实操作系统的进程/DLL 加载运行验证，不得仅靠自带解码器自测，也不得排除特定节来绕过验证。
* 架构设计文档放在 `docs/design/`，带日期的逆向依据与计划放在 `docs/notes/`，面向用户的文档维护在本 GitBook 章节中。提交记录中不要添加署名尾注（attribution trailers）。
