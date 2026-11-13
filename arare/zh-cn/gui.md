---
description: "用于构建、预览和批量运行 arare protect 与 verify 任务的 WPF 桌面前端。"
icon: window-maximize
---

# 桌面 GUI

`Arare.Gui.exe` 是基于 Windows Presentation Foundation（WPF）构建的桌面前端，可根据任务队列拼装 `arare protect` 命令行、实时预览完整的 CLI 调用，并按顺序执行批量加壳与可选的加壳后静态解码校验。

## 编译与启动

从源码编译需要 .NET 10 SDK；直接运行打包好的 GUI 需要对应版本的 .NET 10 Desktop Runtime。

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui -c Release
```

可将 `Arare.Gui.exe` 与 `arare.exe` 放在同一目录（或确保 `arare.exe` 在 `PATH` 中），也可点击底部状态栏的 **Locate…** 手动指定其他 `arare.exe`。启动时传入文件或目录参数即可预填充队列：

```powershell
Arare.Gui.exe app.exe game_folder\
```

* **文件夹选择器：** 未勾选子目录递归时，仅扫描所选根目录以及最多三层深度内的 `Managed` 和 `Plugins` 子目录；勾选子目录递归后会遍历整棵目录树。
* **命令行位置参数：** 通过启动参数传入的文件夹固定采用非递归规则（根目录加三层以内的 `Managed`/`Plugins`），不受已保存的子目录递归复选框影响。

## 队列、参数覆盖与结果校验

* **逐行配置推荐：** 根据 PE 头部自动预选布局配置（`x86` -> `pe32`，`x64` -> `pe64-modern`，`AnyCPU` 托管模块 -> `pe32`；`legacy-dll` 仅限 64 位 DLL 选择）。
* **输出路径与冲突拦截：** 输出默认写入各输入文件同级的 `.\arare-protected\` 目录（也可统一指定单个输出目录）。若存在重复输出路径，或任意输出（含 `._` 伴随文件）会覆盖队列中的输入文件，即使勾选了 **Replace existing outputs**，程序也会在运行前直接拦截。
* **生效配置展示：** 环境检查、页面加密、scribble 与 **ErrLog** 邮件槽上报（`--errlog`）复选框会实时显示当前模块类型的默认生效状态（包括 `disk-integrity` 自动取代 `clean-code` 的联动关系），高亮标出单行手动覆盖项，并提供一键重置按钮。`--antidebug-av` 不在界面中单独列出，直接沿用 CLI 按模块类型的默认设置（EXE 为 `on`，DLL 为 `off`）。
* **脚本导出与批量执行：** 点击 **Copy as .ps1** 会生成可直接运行的 PowerShell 脚本，自动创建输出目录、调用 `arare protect`（及可选的 `arare verify`），并在退出码非零时立即中止。点击 **Protect 1 file** / **Protect N files** 按顺序执行队列；点击 **Cancel** 会在当前条目处理完成后停止后续任务。
* **独立校验：** **Verify existing…** 在不启动目标程序的前提下遍历候选配置，对已加壳文件执行 `arare verify`；勾选 **Check encoding after protect** 则会在每个加壳任务完成后自动调用 `arare verify`。
* **保存配置：** 界面偏好保存在可执行文件同目录的 `Arare.Gui.settings.json` 中；任务队列本身仅在当前会话内保留。

## 冒烟测试

```powershell
dotnet run --project gui/Arare.Gui.SmokeTests -c Release
```

测试套件覆盖 PE 分类、CLI 参数拼装、按模块类型的默认值与覆盖状态解析、`.ps1` 脚本导出、路径冲突检查、基于 Mock 后端的加壳/校验状态切换、运行中关闭窗口确认、目录扫描深度规则及配置保存。许可证为 `AGPL-3.0-only`。
