---
description: "由 HtdpsCmnGetFileInfo 手动映射的内嵌辅助 DLL 目录与职责。"
icon: layer-group
---

# 手动映射辅助模块

CrackProof 不会将主要运行时子系统直接放进受保护程序自身的节内，而是将辅助 DLL 内嵌在加载器载荷中，由内部加载函数 `HtdpsCmnGetFileInfo` 按双字母模块代号手动映射到内存。

## 子模块目录

`HtdpsCmnGetFileInfo` 将目标辅助 DLL 手动映射至私有可执行内存（不挂入 `PEB` 加载器链表，因此遍历 `InLoadOrderModuleList` 或调用 `CreateToolhelp32Snapshot` 均无法枚举到），从其 PE 头部解析入口点，并可在映射完成后抹除其 `MZ` 与 `PE\0\0` 签名：

| 双字母代号 | 模块名 | 状态码区间 | 运行期职责 |
| --- | --- | --- | --- |
| `it` | `HtpecIt.dll` | `Axx` | 用户态防篡改、反注入、虚拟机注册表检查与宿主进程校验 |
| `dt` | `HtdpStub2.dll` | `8xx` / 缺页触发时 | 按需页解密缺页处理模块（`KiUserExceptionDispatcher` 跳转目标）及单页描述符表 |
| `cm` | （用户态辅助模块） | `Bxx` | 第一代 `Htsysm` 驱动部署与初始化 |
| `dm` | （用户态辅助模块） | `Cxx` | 第二代与第三代 `Htsysm` 驱动部署及 IOCTL 握手 |
| `sk` | `HtsyskNT.dll` | `B21` | 第一代内核态 DLL：内核手动映射器及内存/I/O 原语 |
| `pm` | `HtpecmNT.dll` | `BB0` | 第一代内核态 DLL：进程监控与强行终止 |

由于页面解密例程与区域/页面描述符数组均归 `dt`（`HtdpStub2.dll`）管理（详见 [页面保护与加载器代码](page-protection.md)），仅转储主 `.exe` 或 `.dll` 模块会完全漏掉缺页处理逻辑；分析时需在私有可执行 VAD 区间中定位 `dt`，或顺着 `ntdll!KiUserExceptionDispatcher` 开头的内联跳转追踪过去。对应的内核侧组件见 [Htsysm 内核组件](kernel-components.md)。
