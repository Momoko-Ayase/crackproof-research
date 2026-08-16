---
description: "已观察到的 Htsysm 代际、内核职责与版本标记。"
---

# Htsysm 内核组件

## Htsysm 第一代：无鉴权的内核 shellcode（HtsysmNT）

最旧驱动的招牌特性是一个**让任意进程执行内核态 shellcode 的无鉴权 IOCTL**。CrackProof 用它手动映射内核态 DLL（`HtsyskNT.dll`，然后是 `HtpecmNT.dll`），并调用它们的 `_FarEntry@0` 导出——其实现其余内核功能，包括按模块说明的监视并终止分析进程。

其安全姿态名副其实地糟糕：系统上的任何进程都能要求该驱动在 ring 0 运行任意代码。

## Htsysm 第二代：EPROCESS 编辑（Htsysm7679）

第二代在意图上受限得多：它让进程**写自己的 `EPROCESS`**，允许它编辑关于自身的信息。CrackProof 只使用其中一个特性：设置 **Protected Process（PP）标志**，使用户态工具无法打开、读取或注入受保护进程（状态 `C03`/`C04`）。

另外两个细节：

- 某些 API 在 PP 下行为异常（`NtCreateSection` 在列），因此加载器钩住这些函数：临时摘掉 PP 标志、调用原函数、再重新启用。被钩函数列表出现在调试日志中。
- 访问“鉴权”是一种按进程 ID 的加密方案——但任何能正确加密自身进程 ID 的程序都获得同样的 `EPROCESS` 写原语，等价于任意内核内存访问。第二条滥用路径：在进程获得 PP 之前注入 DLL，然后让注入代码享受受保护状态。尽管如此，该驱动仍带着有效的 WHQL 签名发布，成为实用的自带漏洞驱动（BYOVD）候选。

解除 PP 标志需要内核级手段（内核或虚拟机监控器调试器、PP 切换驱动，或在标志设置前钩住 `DeviceIoControl`）。

## Htsysm 第三代：句柄限制（Htsysm767901）

最新一代完全放弃了授予权限的做法。它改为**拒绝未批准进程以危险访问权打开受保护进程的句柄**：`PROCESS_CREATE_THREAD`、`PROCESS_VM_OPERATION`、`PROCESS_VM_READ` 与 `PROCESS_VM_WRITE`。获批进程是固定的系统二进制白名单（`svchost.exe`、`csrss.exe`、`lsass.exe`、`conhost.exe`）。

这一代的鉴权检查比前代更彻底，不授予受保护进程任何特殊权力，对恶意软件也没有利用价值——是这条驱动线上第一个把自己限定在防御上的设计。

## `0x7679` 版本戳

驱动名中编码了构建戳：`Htsysm7679` 与 `Htsysm767901`（即 `7679` 变体 `01`）。同一 dword `0x00007679` 也出现在受保护文件内部，作为 32 位加载器最终阶段的**配置簇戳**（见[分阶段加载器](../loading/README.md)），以及 stage-5 标记表内一个 8 字节标签的一半。它充当把受保护构建与其驱动世代联系起来的版本标识符，在分类未知样本时是有用的指纹。

## 速查

| 组件 | 种类 | 用途 |
| --- | --- | --- |
| `HtpecIt.dll` | 手动映射用户态 DLL | 防篡改/注入/VM 检查（`Axx` 阶段） |
| `HtdpStub2.dll` | 手动映射用户态 DLL | 加载器扩展；页错误按需解密处理器 |
| `HtsyskNT.dll` | 内核 DLL（经第一代驱动） | 内核手动映射器与 I/O（`B21`） |
| `HtpecmNT.dll` | 内核 DLL（经第一代驱动） | 进程监控/终止（`BB0`） |
| HtsysmNT | 内核驱动，第一代 | 无鉴权内核 shellcode IOCTL |
| Htsysm7679 | 内核驱动，第二代 | `EPROCESS` 写；Protected Process 标志 |
| Htsysm767901 | 内核驱动，第三代 | 句柄访问权限制 |

