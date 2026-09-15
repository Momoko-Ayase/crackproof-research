---
description: "Android 记录流使用的算术、模块、容器和压缩层。"
---

# 数据变换

Android 格式把外层首部的算术变换与容器记录的模块变换组合起来。压缩是独立的一层，必须同时校验输入消耗量和输出长度。

- [词、流与记录密码](word-and-record.md) 覆盖 GF(2³²) 混合以及流/记录头。
- [模块配置](module-config.md) 是 `0x9B` 的种子与 AES 材料。
- [容器变换](container.md) 展开 `0x9D` 段。
- [Huffman 与 LZ 压缩](compression.md) 是 writer 格式，与 Windows 家族共享。

本组只描述可观察字段和公式，不为格式中没有出现的中间状态另造名称。
