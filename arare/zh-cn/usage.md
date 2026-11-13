---
description: "命令行 protect、inspect 与 verify：布局配置、环境检查、页面加密与调试日志。"
icon: terminal
---

# 命令行用法

构建 `arare-cli` 即可生成 `target/release/arare.exe`，无需检出 Senbei 仓库。对托管程序集加壳还需安装 .NET 10 运行时，并将三个托管工具文件（`Arare.ManagedHost.dll`、`Arare.ManagedHost.runtimeconfig.json`、`Arare.Bootstrap.dll`）放在 `arare.exe` 同级的 `managed/` 目录中，或通过环境变量 `ARARE_MANAGED_TOOLS` 指定其路径（详见 [开发指南](development.md)）。图形界面批处理用法见 [桌面 GUI](gui.md)。

```text
arare protect INPUT -o|--output OUTPUT --profile PROFILE
    [--seed 64_HEX_DIGITS] [--no-compression]
    [--storage embedded|companion] [--check NAME=on|off]...
    [--page-encrypt on|off] [--scribble on|off]
    [--errlog on|off] [--antidebug-av on|off]
    [--force] [--json]

arare inspect INPUT [--json]

arare verify INPUT --profile PROFILE [--companion PATH] [--json]
```

## 布局配置与载荷存储

| 配置名称 | 目标结构布局族 |
| --- | --- |
| `pe32` | PE32 x86 原生映像，以及受支持的 x86/AnyCPU 托管程序集 |
| `pe64-classic` | 带特征标记的经典 EXE 风格 PE32+ x64 EXE 与 DLL |
| `pe64-modern` | 无特征标记的新式 EXE 风格 PE32+ x64 EXE 与 DLL |
| `legacy-dll` | 旧式专用 PE32+ x64 DLL 布局（仅限内嵌存储） |

配置名称对应二进制结构布局族，而非商业产品的版本号；输入约束详见 [支持范围](support.md)。

* **伴随文件存储（`--storage companion`）：** 同时写出 `OUTPUT`（4 KiB 头部与明文保留区存根）和 `<OUTPUT>._`（加密载荷，通过 `0x1000..0x1020` 处的 32 字节头部配对）。部署时需将两个文件放在同一文件夹中。
* **随机种子与压缩：** 省略 `--seed` 时从 Windows CSPRNG 获取 32 字节随机数并打印十六进制种子。`--no-compression` 让应用程序各节数据块保持未压缩存储，加载器自身的阶段编码仍保持不变。
* **静态校验（`verify`）：** 使用 Arare 独立的原生解码器静态解码受保护文件，不会执行目标程序。省略 `--companion` 时，若同目录下 `<INPUT>._` 的 32 字节头部匹配，`verify` 会自动将其配对。

## 环境检查与失败响应

受保护模块按三个启动阶段运行可配置的环境检查（阶段 1 在载入文件载荷前执行，阶段 2 在载入后执行，阶段 3 在可执行页设为 `PAGE_NOACCESS` 后执行）。可重复传入 `--check NAME=on|off` 覆盖默认值：

| 模块类型 | 默认开启的检查项 |
| --- | --- |
| 原生 EXE | `antidebug`, `crc-loader`, `debug-port`, `os-version`, `boot-options`, `vm-registry`, `injected-dll`, `injected-thread`, `clean-code` |
| 原生 DLL | `crc-loader`, `vm-registry`, `host-process` |
| 托管 EXE | `crc-loader`, `vm-registry` |
| 托管 DLL | `crc-loader`, `vm-registry`, `host-process` |

由于两类 DLL 默认均开启 `host-process`，若要在未加壳的宿主进程内加载受保护 DLL，加壳时需指定 `--check host-process=off`。`vm-backdoor`、`parent-process` 与 `hyperv-guest` 在所有模块类型下均默认关闭。

| CLI 检查名称 | 阶段码 | 行为说明 |
| --- | --- | --- |
| `antidebug` | `410` | 7 个子阶段：`IsDebuggerPresent`、`PEB.BeingDebugged`、`PEB.NtGlobalFlag & 0x70`、硬件调试寄存器 `DR0`..`DR3` / `DR7 & 0xFF`（`GetThreadContext`），以及 `NtQueryInformationProcess`（`ProcessDebugPort`、`ProcessDebugFlags == 0`、`ProcessDebugObjectHandle`） |
| `crc-loader` | `510` | 加载器代码 CRC-32 自校验 |
| `debug-port` | `520` | 内核调试端口查询 |
| `kernel-debugger` | `52F` | `KdDebuggerEnabled` 与系统内核调试器检查 |
| `vm-backdoor` | `540` | VMware `0x5658` I/O 端口探测（忽略通用 CPUID hypervisor 标志位，放行 Hyper-V/VBS） |
| `hyperv-guest` | `541` | Arare 特有的 Hyper-V 客户机分区权限检查（`Hv#1` CPUID） |
| `parent-process` | `A03` | 拒绝父进程不是 `explorer.exe` 或 `cmd.exe` 的启动 |
| `os-version` | `C00` | 要求 Windows 10 build `10240` 或更高版本 |
| `boot-options` | `C01` | 拒绝启用测试签名或调试引导标志的系统 |
| `msc-log` | `BD0` | 检测到 `C:\Windows\msc.log.log` 存在时拒绝运行 |
| `os-compat` | `B00` | 操作系统兼容性检查 |
| `vm-registry` | `A09` | 检查系统硬件/BIOS 虚拟机注册表特征（当 `Hv#1` 识别为 Hyper-V/VBS 时放行通用的 `Virtual` / `VRTUAL` / `Microsoft Hyper-V`） |
| `injected-dll` | `A0F` | 在跳转 OEP 前扫描已加载模块 |
| `injected-thread` | `A07` / `A01` | 检测非预期的外部注入线程 |
| `host-process` | `A11` | 要求宿主进程为兼容的 Arare EXE（带 `.arldr` 或 `.armclr` 标记） |
| `host-stamp` | `A11` | 在 `host-process=on` 时可选开启的协作式运行时上下文标记校验 |
| `clean-code` | `A08` | 通过干净的系统 DLL 代码副本转发加载器调用 |
| `disk-integrity` | `A04` | 同时指定时也会取代 `clean-code`；额外比对内存中映射的系统 DLL 与磁盘上的系统映像 |
| `legacy-debugger` | `BE0` | 旧式调试器设备对象探测 |
| `openark-device` | `E55` | 代码页加密锁定后的 OpenArk 驱动设备检查 |
| `cheat-engine-device` | `E91` | 代码页加密锁定后的 Cheat Engine 驱动设备检查 |

{% hint style="warning" %}
**如无明确需求，请勿开启 `hyperv-guest`。** `--check hyperv-guest=on` 会通过 `Hv#1` CPUID 分区权限识别并拦截客户机虚拟机，同时放行宿主机根分区及 VBS 环境。由于 Hypervisor 的 CPUID 叶可被屏蔽或伪造，应仅将 `hyperv-guest` 视为运行环境限制，而非防篡改手段。
{% endhint %}

**失败响应（`--antidebug-av`）：** `--antidebug-av` 对 EXE 默认为 `on`，对 DLL 默认为 `off`（原生模块日志中分别记为 `-AV=ON` / `-AV=OFF`）。当开启 `--antidebug-av=on` 的原生模块检查未通过时，运行时会先关闭日志，依次调用 `RaiseException(0xC0000005)`（`EXCEPTION_ACCESS_VIOLATION`）并向空指针写入，使附加的调试器立即中断，最后调用 `TerminateProcess(0xE0A00000 | substage)`。设为 `--antidebug-av=off` 的原生模块与托管模块则直接调用 `TerminateProcess`。

## 页面加密

`--page-encrypt` 对 EXE 默认为 `on`，对 DLL 默认为 `off`。节重建完成后，运行时会原地重加密应用程序可执行页，将其设为 `PAGE_NOACCESS`，并 hook `ntdll!KiUserExceptionDispatcher`，在页面首次触发执行异常时按需解密。开启页面加密时，若输入包含可写可执行（`RWX`）节或节对齐小于 `0x1000`，加壳阶段会直接拒绝。

`--scribble=on`（默认 `off`，需配合 `--page-encrypt=on`）会在两次页异常之间对已解密常驻页的部分字节施加掩码。

## 调试日志与 `ErrLog-Pec`

`protect --json`（及标准终端输出）会给出该模块的 12 位十六进制 `log_folder` 名称。若 `%TEMP%\<log_folder>` 目录存在且创建时间不超过 48 小时，模块运行时会写入状态日志（EXE 文件名为 `HHMMSSmmmE-...`，DLL 为 `HHMMSSmmmD-...`），并在末尾输出 `AAA-BBB-CCC` 结束摘要码。

{% hint style="info" %}
**DLL 日志门控继承规则。** 当受保护 DLL 加载到受保护的 Arare EXE 进程内时，即使两者的种子不同，甚至显式设置了 `host-process=off`，DLL 也始终沿用宿主 EXE 的日志上下文。只要宿主 EXE 对应的 `%TEMP%` 目录不存在或已超过 48 小时，即使提前创建了 DLL 自身的备用 `log_folder`，DLL 也不会写出日志。
{% endhint %}

`--errlog=on`（默认 `off`）不受 `%TEMP%` 目录门控限制，会在结束时向邮件槽 `\\.\mailslot\ErrLog-Pec<suffix>`（`<suffix>` 为 `((key + 1) * 0x3039) % 0x8003` 生成的四位十六进制数）发送诊断数据包，内含时间戳、`AAA-BBB-CCC` 状态码及模块与系统信息。

## 输出写入与 JSON 报告

输出文件先在内存中完整编码，随后写入同目录临时文件、同步写入磁盘后执行原子重命名（覆盖已有文件需传入 `--force`）。指向输入文件本身的符号链接或规范化路径别名会被拒绝；替换指向同一文件的其他硬链接条目时，原输入文件字节不受影响。

<details>
<summary>JSON 输出字段（protect、inspect、verify）</summary>

* **`protect --json`：** `output`, `profile`, `storage`, `architecture`, `module`, `input_size`, `output_size`, `seed`, `normalizations`, `log_folder`, `companion`, `companion_size`。
* **`inspect --json`：** `architecture`, `module`, `entry_point`, `image_base`, `image_size`, `file_size`, `sections`（含 `name`, `rva`, `virtual_size`, `raw_offset`, `raw_size`, `characteristics`）。
* **`verify --json`：** `valid`, `profile`, `companion`, `image_size`, `recovered_file_size`, `entry_point`。
</details>
