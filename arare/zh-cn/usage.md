---
description: "命令行保护、检查与验证：配置文件、检查项、页加密与发布。"
---

# 用法

普通构建产出 `target/release/arare.exe`，不需要 Senbei 检出。托管打包需要另行构建的托管工具与 .NET 10 运行时。把三个托管工具文件放入 `arare.exe` 旁的 `managed/` 目录，或把 `ARARE_MANAGED_TOOLS` 设为这些文件所在的绝对目录；详见[开发](development.md)。生成相同命令行的 WPF 前端见[图形界面](gui.md)。

```text
arare protect INPUT --output OUTPUT --profile PROFILE
    [--seed 64_HEX_DIGITS] [--no-compression]
    [--storage embedded|companion] [--check NAME=on|off]...
    [--page-encrypt on|off] [--scribble on|off] [--errlog on|off]
    [--force] [--json]

arare inspect INPUT [--json]

arare verify INPUT --profile PROFILE [--companion PATH] [--json]
```

| 配置 | 输入族 |
| --- | --- |
| `pe32` | PE32 x86/原生，以及适用的 x86/AnyCPU 托管映像 |
| `pe64-classic` | 经典 EXE 式 PE32+ x64 EXE 与 DLL |
| `pe64-modern` | 无标记 EXE 式 PE32+ x64 EXE 与 DLL |
| `legacy-dll` | 专用的较旧 PE32+ x64 DLL 族 |

选定的族会对照输入验证。它不对应公开的商用版本号。各族内的限制见 [支持范围](support.md)。

伴生存储产出命名的 PE 及其匹配的 `<filename>._` 文件。两者须放在一起。覆盖已有输出需要 `--force`。省略种子时使用 Windows 密码学随机源，并在成功时打印。`--no-compression` 以原始形式存储应用程序块；必要的格式与生成的加载器阶段仍使用各自的表示。

`verify` 用独立的原生解码器检查表示。它不启动程序。伴生验证会在 32 字节配对头匹配时自动尝试 `<INPUT>._`。该自动文件缺失时会给出提示。

## 环境检查

受保护模块在启动期间运行可配置的环境检查。大多数检查在载荷重建前运行；可选的 E55/E91 设备检查在页密封后运行。检查失败时静默结束进程。启用日志时，调试日志会记录检查的阶段码。大多数阶段码遵循已观察到的 CrackProof 行为；`541` 是 Arare 自己的 Hyper-V 来宾策略。

默认启用的检查如下：

| 模块 | 检查 |
| --- | --- |
| 原生 EXE | `antidebug`、`crc-loader`、`debug-port`、`os-version`、`boot-options`、`vm-registry`、`injected-dll`、`injected-thread`、`clean-code` |
| 原生 DLL | `crc-loader`、`vm-registry`、`host-process` |
| 托管 EXE | `crc-loader`、`vm-registry` |
| 托管 DLL | `crc-loader`、`vm-registry`、`host-process` |

其余检查默认关闭。因此两类 DLL 默认都需要兼容的受保护 EXE。`vm-backdoor`、`parent-process` 与 `hyperv-guest` 对所有模块类型都需要显式启用。

`--check NAME=on|off` 切换单项检查。重复该标志以组合覆盖。

| 名称 | 阶段 |
| --- | --- |
| `antidebug` | 410 |
| `crc-loader` | 510 |
| `debug-port` | 520 |
| `kernel-debugger` | 52F |
| `vm-backdoor` | 540 |
| `hyperv-guest` | 541（Arare 专用） |
| `parent-process` | A03 |
| `os-version` | C00 |
| `boot-options` | C01 |
| `msc-log` | BD0 |
| `os-compat` | B00 |
| `vm-registry` | A09 |
| `injected-dll` | A0F |
| `injected-thread` | A07/A01 |
| `host-process` | A11 |
| `host-stamp` | 可选的 A11 运行时上下文校验 |
| `clean-code` | A08 |
| `disk-integrity` | A04 |
| `legacy-debugger` | BE0 |
| `openark-device` | E55 |
| `cheat-engine-device` | E91 |

`vm-backdoor` 仍需显式启用。`--check vm-backdoor=on` 探测 VMware 后门协议，并在收到匹配响应时拒绝运行。它允许 Hyper-V/VBS 环境；通用的 CPUID 虚拟机监控程序标志位不会触发拒绝。显式指定 `--check parent-process=on` 仍会拒绝除 `cmd.exe` 或 `explorer.exe` 以外的启动器。

**强烈不建议启用：** `hyperv-guest` 是独立检查，对所有模块类型默认关闭。`--check hyperv-guest=on` 根据经校验的 `Hv#1` CPUID 分区权限拒绝报告为 Hyper-V 兼容来宾的环境。它允许主机/根分区（包括 VBS），也允许无法判断或信息不完整的环境。来宾检测依赖启发式判断，嵌套环境、信息屏蔽或伪造都可能绕过分类。这是兼容性限制，不能提供可靠保护。

`vm-registry` 默认仍然启用。当 `Hv#1` 接口表明环境兼容 Hyper-V 时，该检查允许 `Virtual`、`VRTUAL` 与 `Microsoft Hyper-V` 这些通用注册表标记。其他虚拟机厂商的明确标记仍会触发拒绝。是否拒绝 Hyper-V 兼容来宾，由独立且需显式启用的 `hyperv-guest` 决定。

已有受保护文件保留生成时使用的检查实现。要应用修订后的检查与默认值，使用更新后的构建重新保护原始输入。GUI 或命令脚本中保存的显式 `on` 覆盖仍然有效；对于不需要的可选限制，清除覆盖或将其设为 `off`。

`host-process` 接受兼容的原生与托管 Arare EXE，包括不同打包种子。用 `--check host-process=off` 可在普通主机中加载受保护 DLL。`host-stamp` 只为已启用 `host-process` 的 DLL 增加校验。可选戳记是协作式运行时兼容性检查，不是密码学认证。

启用 `disk-integrity` 会取代 `clean-code`，即使同时指定两者。两者都会把加载器调用路由到原始系统代码副本；`disk-integrity` 还会对照可信系统映像校验磁盘映像。

`os-version`（C00）使用 Arare 的下限：Windows 10 内部版本 10240。一份已观察的商用样本使用 14251。

`legacy-debugger`、`openark-device` 与 `cheat-engine-device` 为可选，默认关闭。仅凭布局族名称不能确定商用构建的选项默认值。

## 页加密

`--page-encrypt=on` 时，加载器在重建后把可执行应用程序页就地重新加密，并设为 `PAGE_NOACCESS`。stub 模块的处理程序在首次触及时解密该页。页密文在运行时创建；文件载荷仍使用所选格式的编码。默认情况下主机 EXE 开启、DLL 关闭，与已观察到的配置一致。

`--scribble=on` 在故障之间对驻留已解密页的选定字节做 XOR。它要求页加密，默认关闭。

`--errlog=on` 尝试向 `\\.\mailslot\ErrLog-Pec<suffix>` 发送诊断报告，其中 `<suffix>` 是根据日志身份派生的四位十六进制数。报告包含时间戳、结束码 `AAA-BBB-CCC` 与模块路径；失败报告还可能包含已加载模块或 OS 详情。该通道独立于调试日志文件夹，默认关闭；只有匹配的邮件槽存在监听方时才能送达。

含可写可执行节的输入需要 `--page-encrypt=off`。有效的默认开启与显式开启会在发布或替换任一输出之前拒绝它们。

## 调试日志

`protect --json` 返回 `log_folder`，即模块自身的 12 位大写十六进制日志身份。在 `%TEMP%` 下创建该文件夹即可启用其日志。创建时间须在 48 小时内。运行时不会创建缺失的门控目录。

DLL 跨打包种子继承其受保护 EXE 的门控与文件夹。主机门控缺失、过期或无效时，即使 DLL 自己的门控是新的，也会抑制 DLL 日志。没有受保护主机上下文时，DLL 使用自己的门控。使用受保护主机时，应采用 EXE 报告的 `log_folder`；DLL 报告的值标识其后备文件夹。

主机校验与日志相互独立：`host-process=off` 不会关闭继承。EXE 使用 `HHMMSSmmmE-...` 文件名，DLL 使用 `HHMMSSmmmD-...`。

## 输出

保护会在发布前解析并编码完整表示。输出文件先暂存、刷新，再重命名。目标目录必须已经存在。输入的规范路径或符号链接别名会被拒绝。替换不同硬链接上的输出会替换该目录项，并保留输入字节。

固定种子会为相同输入、选项与已编译加载器复现输出。更换编译器、运行时源码或元数据写入器可能改变字节。
