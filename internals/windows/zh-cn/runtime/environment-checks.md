---
description: "运行期调试器、虚拟机、系统完整性、注入模块与线程、A11/A15 宿主及反 Hook 检测。"
icon: user-shield
---

# 环境与反分析检测

CrackProof 的启动检测贯穿第一阶段（载荷展开前）、`C`/`B`/`A` 调度轮次以及页面加密锁定后的可选 `E` 系列检查：

{% tabs %}
{% tab title="调试器" %}
* **`410`（用户态反调试）：** 检查 `IsDebuggerPresent`（实机采样显示商业版 `410` 内部没有基于 SEH 的子阶段；单步陷阱标志 `#DB` 的 SEH 诱饵单独分布在 Stage 5 加载器代码中）。
* **`520` 与 `52F`：** 通过 `NtQueryInformationProcess` 查询调试相关的信息类（`520`）以及内核调试器状态（`52F`）。
* **`BE0`：** 检查旧式 SoftICE / Syser 驱动设备名。
* **计时与 `#DB` 诱饵：** Stage 5 交错插入 `in eax, dx` 计时读取指令与 `pushfq; or [rsp], 0x100; popfq` 单步陷阱，由配套的 SEH 处理函数跳过死代码分支（详见 [页面保护与加载器代码](page-protection.md)）。
{% endtab %}

{% tab title="虚拟机" %}
* **`540`（VMware 后门）：** 执行 `0x5658` I/O 端口探测（`in eax, dx`）；该指令在物理机及非 VMware 虚拟化环境下会触发 `#GP` 异常，而在 VMware 中则返回特定魔数。
* **`A09`（硬件注册表前缀）：** 检查 `HKLM\Hardware\Description\System\SystemBiosVersion`、`HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation\SystemProductName` 与 `HKLM\Hardware\Description\System\BIOS\SystemProductName` 是否以 `Virtual`、`VMware`、`Bochs`、`VBOX`、`VRTUAL`、`Microsoft Hyper-V` 或 `Parallels` 开头（部分构建还会在此处检查 CPU 虚拟化特性位）。
{% endtab %}

{% tab title="系统完整性" %}
* **`C00` 与 `B00`：** 将系统真实构建号（`0x01A00000 + build`）与配置的 Windows 10+ 最低版本要求比对（`C00`，可直接拦截单纯把 PEB 版本号改低的伪造手法），并检查操作系统兼容性（`B00`）。
* **`C01`：** 拒绝开启了 `testsigning` 或 `disableintegritychecks` 启动项的机器。
* **`BD0`：** 若存在 `C:\Windows\msc.log.log` 则直接中止进程。
* **`E55` 与 `E91`：** 在 `1B40` 族系构建中，探测分析工具驱动（如 OpenArk、Cheat Engine）创建的设备符号链接。
{% endtab %}

{% tab title="进程与宿主（A11 / A15）" %}
* **`A03`：** 限制父进程名称（通常仅允许 `explorer.exe` 或 `cmd.exe`）。
* **`A0F`：** 扫描已加载模块（包括 `AppInit_DLLs`、`user32.dll`、`apphelp.dll` 与 `ShimEng.dll`），部分宿主构建还会拒绝应用程序目录下出现的未知 DLL。
* **`A07` 与 `A01`：** 终止非预期的外部线程（`A07`），若有外部线程未能清除则中止进程（`A01`）。
* **`A11`（DLL 宿主校验）：** 检查当前进程中映射的宿主 EXE，只要包含名为 `peC` 的节，或导入描述符引用了大小写完全一致的 `KeRnEl32.dLl`，即视为合法宿主（Windows 加载器解析 DLL 名时不区分大小写，而这一大小写混排字符串正是 CrackProof 宿主的标记）。另有第二种 `A11` 变体还会额外校验一个标志参数。
* **`A15`（DLL 调度标记）：** 不包含实际检查代码；受保护 DLL 在 `A09`/`A11` 通过后，会在 `5D0` 之后输出该状态码。宿主 EXE 从不记录 `A15`（在同一槽位输出 `552`/`570`）。
{% endtab %}

{% tab title="反 Hook" %}
* **`A08` 与 `A04`：** 从 `System32` 映射磁盘上干净的 `ntdll.dll` 与 `kernel32.dll` 副本，拷回未修改的 `.text` 字节以抹除用户态 inline hook；若磁盘上的系统 DLL 文件本身已被改动，`A04` 还会中止运行。
{% endtab %}
{% endtabs %}
