---
description: "根据作业列表生成 arare protect 命令行的 WPF 前端。"
---

# 图形界面

Arare 命令行的 WPF 前端。它根据作业列表生成 `arare protect` 调用，运行前显示确切命令，并按顺序执行作业，可选在保护后验证。

需要 .NET 10 SDK，与托管工具使用的 SDK 相同。

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui
```

把 `Arare.Gui.exe` 放在 `arare.exe` 旁边。图形界面先在自身旁边查找 `arare.exe`，再查 `PATH`。探测失败时可在状态栏选择其他位置。

位置参数会预先加入文件与文件夹：

```powershell
Arare.Gui.exe app.exe game_folder\
```

文件夹扫描规则与文件夹选择器相同：根目录，加上最多三层深的 `Managed` 或 `Plugins` 目录。

## 行为

- 每一行作业拥有自己的保护配置。建议配置来自 PE：x86 对应 `pe32`，x64 对应 `pe64-modern`，AnyCPU 托管映像对应 `pe32`。`legacy-dll` 只对 64 位 DLL 有效。
- 输出默认写到各输入旁的 `.\arare-protected\`，或写到选定的输出文件夹并保留文件名。
- 环境检查、页加密与 scribble 跟随命令行按模块类型的默认值，包括 `disk-integrity` 取代 `clean-code` 的规则。复选框显示所选行的解析状态；覆盖某选项会做标记并提供复位。
- 命令预览始终对应当下将要运行的内容。它使用虚拟化，因此含数千个文件的文件夹仍能保持响应。
- 保护按顺序运行作业，可在文件之间取消。启用“保护后检查编码”时，每个输出用 `arare verify` 检查。该解码器检查不启动程序。
- 设置保存在可执行文件旁的 `Arare.Gui.settings.json`。作业列表不会持久化。

## 测试

```powershell
dotnet run --project gui/Arare.Gui.SmokeTests
```

覆盖 PE 分类、命令构造、覆盖/默认模型、预览生成、校验、针对假后端的保护/验证流程、运行中关闭握手、文件夹扫描规则与设置持久化。

许可证为 AGPL-3.0-only，与命令行一致。
