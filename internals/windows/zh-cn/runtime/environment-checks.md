---
description: "控制权到达原程序前执行的用户态与内核辅助检查。"
---

# 环境与反分析检查

检查在解密之前（部分与解密交错）运行。按目标分组：

**调试器。** 用户态检查从 `410` 开始，包括 `IsDebuggerPresent` 和 `NtQueryInformationProcess`（`520`）。另外还有内核调试器检查（`52F`）、SoftICE/Syser 时代检查（`BE0`），以及[页保护与加载器代码](page-protection.md#加载器自身的代码多态与诱饵)中计时敏感的诱饵。VMware 后门探测（`540`）同时充当模拟器检查：`in eax, dx` 后门指令在真实硬件与多数模拟器上出错，但在 VMware 下返回一个魔数。OS 版本检查（`C00`）读的是真实版本；把 PEB 里的 OS 版本字段改成更低的值会在 `C00` 失败。

**虚拟机。** 注册表字符串检查（`A09`）针对三个值（`HKLM\Hardware\Description\System\SystemBiosVersion`、`HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation\SystemProductName` 与 `HKLM\Hardware\Description\System\BIOS\SystemProductName`），在值的开头匹配：`Virtual`、`VMware`、`Bochs`、`VBOX`、`VRTUAL`、`Microsoft Hyper-V`、`Parallels`。同一阶段有时检查 CPU 特性标志（要求硬件虚拟化暴露给客户机）。

**系统完整性。** OS 最低/兼容版本检查（`C00`/`B00`）、针对 `testsigning` 或 `disableintegritychecks` 的启动选项检查（`C01`，它会挡住常见的未签名驱动分析环境），以及确保 `C:\Windows\msc.log.log` 不存在的检查（`BD0`）。部分 `1B40` 家族构建还会把正在运行的驱动设备名和一份短名单比较（`E55`、`E91`）。

**进程完整性。** 注入 DLL 清扫（`A0F`）已观察会查看 `AppInit_DLLs`、`user32.dll`、`apphelp.dll` 和 `ShimEng.dll`；先杀（`A07`）再在残留时中止（`A01`）的注入线程清扫；父进程策略（`A03`）；以及，对受保护 DLL，宿主进程检查（`A11`），寻找宿主中保护器自身的标记（`peC` 节，或来自 `KeRnEl32.dLl` 的导入）。部分宿主可执行文件还会拒绝自己目录里多出来的 DLL。`A07` 清扫决定了进程内分析辅助代码要么在此之前运行、要么睡过它。

**反钩子。** 在 `A08`/`A04`，加载器把磁盘上纯净系统 DLL 中 ntdll/kernel32 的*代码*拷入内存并优先使用之，挫败对这些模块的用户态内联钩子；`A04` 在磁盘映像本身被补丁时中止。

