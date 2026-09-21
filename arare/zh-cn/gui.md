---
description: "根据作业列表生成 arare protect 命令行的 WPF 前端。"
---

# 图形界面

Arare 命令行的 WPF 前端。它根据作业列表生成 `arare protect` 调用，运行前显示确切命令，并按顺序执行作业，可选在保护后验证。

构建需要 .NET 10 SDK，与托管工具使用的 SDK 相同。打包后的图形界面需要对应包架构的 .NET 10 Desktop Runtime。原生命令行只在打包托管输入时需要 .NET。

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui
```

把 `Arare.Gui.exe` 放在 `arare.exe` 旁边。图形界面先在自身旁边查找 `arare.exe`，再查 `PATH`。探测失败时，选择状态栏中的 **Locate…** 指定其他位置。

位置参数会预先加入文件与文件夹：

```powershell
Arare.Gui.exe app.exe game_folder\
```

关闭子文件夹扫描时，文件夹选择器扫描根目录，并递归扫描在最多三层深度内找到的 `Managed` 或 `Plugins` 目录。开启子文件夹扫描会包含所选的整棵目录树。

## 行为

- 每一行作业拥有自己的保护配置。建议配置来自 PE：x86 对应 `pe32`，x64 对应 `pe64-modern`，AnyCPU 托管映像对应 `pe32`。`legacy-dll` 只对 64 位 DLL 有效。
- 输出默认写到各输入旁的 `.\arare-protected\`，或写到选定的输出文件夹并保留文件名。
- 输出路径重复，或输出与任一排队输入重叠的作业会被拒绝。伴生文件也包括在内，即使启用 **Replace existing outputs** 仍适用。对于文件名相同的输入，应使用各自的输出文件夹。
- 环境检查、页加密与 scribble 跟随命令行按模块类型的默认值，包括 `disk-integrity` 取代 `clean-code` 的规则。复选框显示所选行的解析状态；覆盖某选项会做标记并提供复位。
- 命令预览显示选定的命令行路径与保护参数。**Copy as .ps1** 导出把参数视为字面值的 PowerShell 命令，创建输出目录，包含选定的保护后验证，并在命令行返回非零退出码时停止。
- **Protect** 按顺序运行作业。**Cancel** 会让当前文件的保护与可选验证完成，再停止剩余作业。运行期间关闭窗口会先请求确认，并等待该文件完成。
- 启用 **Check encoding after protect** 时，每个输出用 `arare verify` 检查。该解码器检查不启动程序。
- 设置保存在可执行文件旁的 `Arare.Gui.settings.json`。作业列表不会持久化。

## 测试

```powershell
dotnet run --project gui/Arare.Gui.SmokeTests
```

覆盖 PE 分类、命令构造、覆盖/默认模型、预览生成、校验、针对假后端的保护/验证流程、运行中关闭握手、文件夹扫描规则与设置持久化。

许可证为 AGPL-3.0-only，与命令行一致。
