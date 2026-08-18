---
description: CrackProof 所保护 Windows PE 文件的内部结构与运行时行为。
---

# CrackProof for Windows 内部机制

CrackProof for Windows 保护 PE32 与 PE32+ 可执行文件和 DLL。受保护文件保留足以加载自举映像的 PE 外层结构，而原始节、加载器阶段、部分数据目录、名称和代码页则以变换后的形式保存。运行时会在控制权转交给原程序前重建映像。

目前观察到的布局包括原生与托管映像、旧版基于标记的容器、必须按结构识别的新版布局，以及将受保护载荷放在伴生文件中的 stub 可执行文件。

## 约定

* 除非另有说明，所有偏移均为自文件起始的十六进制字节偏移。`u32@X` 表示偏移 X 处的小端 32 位值。
* **RVA**（相对虚拟地址）按 PE 的通常含义使用。加载器在按 RVA 布局的内存映像上工作；在磁盘上，同一偏移也被用作解包后映像缓冲区内的文件偏移。
* 整数运算为固定宽度（32 位或 8 位）回绕运算，与算法来源的 x86 环境一致。Python 参考代码中显式施加掩码。
* 诸如 `info[3]` 的名称指从加密文件头派生的 8-dword 表中的条目（见[受保护文件结构](file-structure/file-format.md)）。

## 内容索引

| 范围              | 起点                                                |
| --------------- | ------------------------------------------------- |
| 磁盘布局与构建识别       | [受保护文件结构](file-structure/file-format.md)          |
| 密码、压缩与校验和       | [数据变换](data-transforms/data-transforms.md)        |
| 加载器阶段与节恢复       | [加载与节恢复](loading-and-pe-repair/loading/)          |
| 头、目录、导入与 CLR 数据 | [PE 重建](loading-and-pe-repair/pe-reconstruction/) |
| 启动检查、页保护与内核组件   | [运行时行为](runtime/runtime.md)                       |
| 分析流程、局限与常量      | [分析笔记](analysis/analysis.md)                      |

Windows 数据变换页面对应的测试代码发布在[验证与参考](https://app.gitbook.com/s/L9bXLua8yrIPEUZOHO21/)中。Huffman/LZ 记号语言与缓冲区内 AES 日程也出现在 [Android 原生库格式](https://app.gitbook.com/s/Aoyn9wKiHAVzBKGSUifa/)中。
