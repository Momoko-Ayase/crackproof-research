---
description: "Android 用户态反分析、NativeBridge、ptrace、内存读取与签名检查。"
icon: user-shield
---

# 环境与完整性检查

与 Windows 产品线不同，Android 上的 CrackProof 完全运行在用户态，没有配套内核驱动。在嵌套记录流逐层展开的过程中，各类环境检查分散在第一阶段、第二阶段以及[运行时模块](modules.md)所列的各个功能模块中执行。

## 进程与 ABI 二进制转译检查

* **自映射与环境变量**：第一阶段解析 `/proc/self/maps` 定位自身磁盘 ELF 文件；第二阶段保留映射上下文并检查 `/proc/self/environ`。
* **ARM-on-x86 二进制转译（NativeBridge）**：检查 `/system/lib/libhoudini.so` 与 `/system/lib64/arm64/nb/` 路径，判断当前进程是否运行在 `ARM-on-x86` 转译层而非原生 AArch64 硬件上。
* **文件系统与 libc 检查**：模块 `0x8F` 检查 `/proc/self/cmdline`、`uid`/`gid`/`tid` 以及文件属主与权限模式；模块 `0x60` 扫描系统库目录与运行时路径；模块 `0x20` 校验目标 ELF 头、`/proc/self/maps` 以及当前 `libc` 映射。

## 守护子进程与 `PTRACE_SEIZE`

已观察到的 IL2CPP 构建会在 ART 与虚拟机库初始化完毕之后、`dlopen` 加载受保护 `.so` 之前，先 `fork` 出一个守护子进程。子进程以 `PTRACE_SEIZE | PTRACE_O_EXITKILL` 附加到父进程，抢占 `ptrace` 调试位，并在任一进程退出时连带终止整个应用。由于 `fork` 发生在受保护 `.so` 加载之前，该共享库永远不会出现在 `/proc/<child>/maps` 中。

## `/proc/<pid>/mem` 监控与页权限

在已观察到的构建上，打开并读取 `/proc/<pid>/mem` 会在数秒内导致进程终止；而在同一批构建上读取 `/proc/<pid>/maps`、`cmdline`、`status`，或通过 `process_vm_readv` 读取进程内存，均未触发进程终止。模块 `0x9B` 完成段还原后，可执行页保持可读状态（`PROT_READ | PROT_EXEC`）；Android 构建未启用类似 Windows 版的 `PAGE_NOACCESS` 按需页加密机制。

## APK 签名与网络时间校验

模块 `0x40` 按签名方案从高到低的顺序校验 `base.apk` 与各 split APK：依次检查 APK Signature Scheme v3.1、v3、v2 以及 JAR 签名（v1）。模块 `0x02` 通过 UDP 123 端口向 NTP 服务器查询网络时间，并将返回时间戳与内置阈值比对。模块 `0x69` 则 `fork` 一个短暂运行的探测子进程并检查其退出状态。

## 脱离动态链接器模块链表

第二阶段各层解释器与功能模块均驻留在匿名 `mmap` 内存区（初始化期间常为 `RWX`），执行完回调后即可将自身内存清零或覆写。与 Windows 上的[手动映射辅助模块](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/runtime/mapped-modules)类似，这些模块都不会出现在 Bionic 的 `dl_iterate_phdr` 遍历结果或 `soinfo` 链表中。
