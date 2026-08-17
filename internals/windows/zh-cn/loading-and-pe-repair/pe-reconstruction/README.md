---
description: "如何把恢复后的内存映像重新组成结构一致的 PE 文件。"
---

# PE 重建

节恢复得到的是按 RVA 组织的内存映像。要形成可用的 PE 文件，还需要协调头、文件偏移、数据目录、导入、TLS 状态、导出、重定位；托管映像还需要恢复 CLR 结构。

- [头、节与零填充范围](memory-image.md)
- [导入、TLS 与导出](imports-tls-exports.md)
- [重定位、页变换与 CLR 数据](relocations-managed.md)

这些步骤依赖具体布局。旧版固定基址可执行文件、需要重定基址的 DLL、外置伴生映像与 CLR 映像不能使用同一种数据目录处理策略。
