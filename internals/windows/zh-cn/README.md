---
description: "CrackProof 加壳 Windows PE 文件的容器结构、数据变换、多阶段还原与运行时机制。"
icon: desktop
---

# CrackProof for Windows 内部机制

CrackProof for Windows 用于保护 PE32（`0x10B`）与 PE32+（`0x20B`）格式的可执行文件和 DLL。加壳后的二进制文件保留合法的外层 PE 头部供系统映射引导加载器，原始应用的各个节、各阶段加载器代码、导入表、CLR 元数据及可执行代码页均经加密或压缩存储。模块加载时，壳运行时先检查宿主环境，在内存中重建映像，按配置通过异常分发 hook 保护可执行页，最后跳转到原始入口点（OEP）。

目前已观测到的构建类型涵盖原生与托管（.NET）的 EXE 和 DLL、64 位有标记与无标记布局、32 位标准壳与紧凑壳、64 位专用 DLL 容器，以及拆分为 4 KiB 存根 PE 与外部 `._` 伴生文件的 PE32+ 模块。

## 约定说明

* 如无特别说明，偏移量均表示相对于文件起始位置的十六进制字节偏移。`u32@X` 表示偏移 `X` 处的小端序 32 位无符号整数。
* **RVA**（相对虚拟地址）遵循标准 PE 定义。静态重建直接在按 RVA 寻址的映像缓冲区上进行（64 位输出保持 `VirtualAddress == PointerToRawData`，32 位输出在写入文件前重新按 `0x200` 文件对齐紧凑排布）。
* 整数运算遵循与 x86 一致的 8 位或 32 位定宽无符号回绕语义，Python 参考代码均显式附带位掩码（`& 0xFF`、`& 0xFFFFFFFF`）。
* `info[0..7]` 表示从文件偏移 `0x1000` 解密得到的 8 个 32 位双字（详见[容器布局与加密头部](file-structure/container-layout.md)）。

## 章节导航

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-folder-tree"></i></td><td><strong>文件结构</strong></td><td><code>0x1000</code> 处的磁盘容器切分、<code>KONN</code> 头部密钥派生、构建类型与外部 <code>._</code> 伴生文件。</td><td><a href="file-structure/file-format.md">受保护文件结构</a></td></tr><tr><td><i class="fa-shuffle"></i></td><td><strong>数据变换</strong></td><td>滚动异或链与循环移位算法、LFSR、字符串与代码页混淆、CRC 与阶段密钥、AES-CBC、Huffman/LZ 压缩及字节码解释器。</td><td><a href="data-transforms/data-transforms.md">数据变换</a></td></tr><tr><td><i class="fa-stairs"></i></td><td><strong>加载流程与节还原</strong></td><td>64 位九阶段还原流水线、PE32 标准/紧凑壳体与专用 DLL 变体，以及无标记布局的结构定位。</td><td><a href="loading-and-pe-repair/loading/README.md">加载流程与节还原</a></td></tr><tr><td><i class="fa-puzzle-piece"></i></td><td><strong>PE 重建</strong></td><td>节头修复、临时解密的入口点与数据目录块、导入表与 <code>.kmiat</code>、TLS、导出表、重定位及 CLR 数据回填。</td><td><a href="loading-and-pe-repair/pe-reconstruction/README.md">PE 重建</a></td></tr><tr><td><i class="fa-play"></i></td><td><strong>运行时行为</strong></td><td>状态日志、<code>AAA-BBB-CCC</code> 错误码、反分析检测、<code>KiUserExceptionDispatcher</code> 页面保护、辅助模块与 <code>Htsysm</code> 驱动。</td><td><a href="runtime/runtime.md">运行时行为</a></td></tr><tr><td><i class="fa-compass"></i></td><td><strong>分析说明</strong></td><td>静态与动态分析流程对比、已知局限、<code>-GMD</code> IL2CPP 元数据方法令牌重映射，以及全局偏移与常量速查表。</td><td><a href="analysis/analysis.md">分析说明</a></td></tr></tbody></table>

本章各项变换算法的可运行 Python 实现与测试向量收录于[验证与参考实现](https://app.gitbook.com/s/L9bXLua8yrIPEUZOHO21/)。相同的 3 字节 Huffman/LZ 令牌编码与缓冲区内嵌 AES 轮密钥表同样见于 [CrackProof for Android SO 内部机制](https://app.gitbook.com/s/Aoyn9wKiHAVzBKGSUifa/)。
