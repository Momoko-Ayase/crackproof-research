---
description: "命令行保护、检查与验证：配置文件、检查项、页加密与发布。"
---

# 用法

普通构建产出 `target/release/arare.exe`，不需要 Senbei 检出。托管打包需要另行构建的托管工具。生成相同命令行的 WPF 前端见 [图形界面](gui.md)。

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

受保护模块在解密前运行 CrackProof 风格的环境检查。每一项记录其观察到的阶段码，失败时静默结束进程。

原生 EXE 使用较完整的已观察检查集。原生 DLL 启用 `crc-loader`、`vm-backdoor`、`vm-registry` 与 `host-process`。托管模块启用 `crc-loader` 与 `vm-registry`；托管 DLL 另外启用 `host-process`。因此两类 DLL 默认都需要兼容的受保护 EXE。

`--check NAME=on|off` 切换单项检查。重复该标志以组合覆盖。

| 名称 | 阶段 |
| --- | --- |
| `antidebug` | 410 |
| `crc-loader` | 510 |
| `debug-port` | 520 |
| `kernel-debugger` | 52F |
| `vm-backdoor` | 540 |
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

默认值按设计会产生误报。`parent-process` 拒绝除 `cmd.exe`/`explorer.exe` 以外的启动器。`vm-backdoor` 拒绝存在虚拟机监控程序的机器，包括 VBS/Hyper-V 主机。这类环境应关闭它们。

`host-process` 接受兼容的原生与托管 Arare EXE，包括不同打包种子。用 `--check host-process=off` 可在普通主机中加载受保护 DLL。可选戳记是协作式运行时兼容性检查，不是密码学认证。

`os-version`（C00）使用 Arare 的下限：Windows 10 内部版本 10240。一份已观察的商用样本使用 14251。

`legacy-debugger`、`openark-device` 与 `cheat-engine-device` 为可选，默认关闭。仅凭布局族名称不能确定商用构建的选项默认值。

## 页加密

`--page-encrypt=on` 时，加载器在重建后把每个可执行应用程序页就地重新加密，并设为 `PAGE_NOACCESS`。stub 模块的处理程序在首次触及时解密该页。文件只携带描述符表，不携带密文。默认与已观察构建一致：主机 EXE 开启，DLL 关闭。

`--scribble=on` 在故障之间对驻留已解密页的选定字节做 XOR。它要求页加密，默认关闭。

`--errlog=on` 在日志关闭时把结束码 `AAA-BBB-CCC` 报告到 `\\.\mailslot\ErrLog-Pec`。默认关闭。

含可写可执行节的输入需要 `--page-encrypt=off`。有效的默认开启与显式开启会在发布或替换任一输出之前拒绝它们。

## 调试日志

在 `%TEMP%` 下创建该构建的 12 位十六进制文件夹以启用日志。其创建时间须在 48 小时内。运行时不会创建缺失的门控目录。

DLL 跨打包种子继承其受保护 EXE 的门控与文件夹。主机门控缺失、过期或无效时，即使 DLL 自己的门控是新的，也会抑制 DLL 日志。没有受保护主机上下文时，DLL 使用自己的门控。

主机校验与日志相互独立：`host-process=off` 不会关闭继承。EXE 使用 `HHMMSSmmmE-...` 文件名，DLL 使用 `HHMMSSmmmD-...`。

## 输出

保护会在发布前解析并编码完整表示。输出文件先暂存、刷新，再重命名。目标目录必须已经存在。输入的规范路径或符号链接别名会被拒绝。替换不同硬链接上的输出会替换该目录项，并保留输入字节。

固定种子会为相同输入、选项与已编译加载器复现输出。更换编译器、运行时源码或元数据写入器可能改变字节。
