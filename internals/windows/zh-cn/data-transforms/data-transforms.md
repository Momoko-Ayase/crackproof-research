---
description: "Windows 头、加载器阶段、名称、节与代码页所用的可逆数据变换。"
---

# 数据变换

CrackProof 并非只使用一种覆盖整个容器的密码，而是叠加多个小型变换。输入范围、地址依赖与执行顺序都很重要：即使对错误范围使用了正确变换，也可能产生看似合理的字节。

各页按用途拆分：

- [滚动密钥与旋转密码](rolling-and-rotation.md)介绍早期阶段与小型记录使用的操作。
- [LFSR、字符串与页变换](lfsr-strings-pages.md)介绍嵌入式指令流、导入名与稀疏代码页变化。
- [校验和与密钥推进](checksums.md)说明记录验证，以及一个结果如何推进下一个密钥。
- [AES-CBC](aes.md)、[Huffman/LZ 压缩](compression.md)与[按构建定制的字节变换](bytecode-transform.md)组成主要的节数据处理路径。
