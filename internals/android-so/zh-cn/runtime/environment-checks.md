---
description: "加载时已观察的 Android 环境、完整性与转储相关检查。"
---

# 环境与完整性检查

Windows 构建把用户态探测与可选的内核支持叠在一起。Android 家族留在用户态。本页的检查来自第一阶段、第二阶段，以及[运行时模块](modules.md)列出的模块。它们在这些嵌套流仍在落地时运行，而不是在已恢复的 ELF 就位之后。

## 进程与翻译环境

第一阶段已经遍历 `/proc/self/maps` 以找到自己的文件。第二阶段保留 maps 上下文，并查看 `/proc/self/environ`。一种已观察探测通过查找 `/system/lib/libhoudini.so` 与 `/system/lib64/arm64/nb/` 下的路径，测试是否存在 x86-on-ARM 翻译层。正在翻译 ARM 代码、而不是原生跑 AArch64 的宿主，因此与加载器所期望的环境不同。

模块 `0x8F` 读 `/proc/self/cmdline`，查询 uid/gid/tid，并检查某路径的属主与模式。模块 `0x60` 扫描系统库目录、进程环境与运行时路径。模块 `0x20` 校验目标路径、ELF 头、`/proc/self/maps` 以及 libc 映射。

## 第二进程与 ptrace

已观察的 IL2CPP 库在 ART 启动且 VM 模块映射之后、受保护库本身加载之前，fork 一个辅助进程。子进程用 `PTRACE_SEIZE` 与 `PTRACE_O_EXITKILL` 抓住父进程。这占住 ptrace 槽位，并把两个进程的寿命绑在一起。因此子进程的 maps 里不会出现受保护库。

## 内存可见性

打开并读取 `/proc/<pid>/mem` 已被观察到会在数秒内杀死进程。读 `maps`、`cmdline` 与 `status` 则不会。同一批构建上 `process_vm_readv` 没有引起这种反应。恢复完成后，可执行页保持可读。没有 Windows 那种对按需出错代码做 `PAGE_NOACCESS` 再加密。

## 包与时间

模块 `0x40` 检查 `base.apk` 与同级拆分 APK。已观察的签名顺序是 v3.1，然后 v3，然后 v2，然后 JAR/v1。模块 `0x02` 发送 UDP 123 端口时间查询，并把答复与配置阈值比较。模块 `0x69` fork 一个子探测并等待其退出状态。

## 缺席的部分

这条路径上没有 Htsysm 一类内核驱动。第二阶段模块是普通用户态映像，常常落在私有 RWX 区域，运行后可以擦掉或改写自己。它们不出现在动态链接器的模块列表里，与 Windows 上[手动映射的辅助模块](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/runtime/mapped-modules)造成的缺口同类。
