---
description: "CrackProof 所保护 Android 原生库的内部结构与恢复规则。"
---

# CrackProof for Android SO 内部机制

本 Space 记录 CrackProof Android 原生库格式，范围包括 ELF64 小端 AArch64 文件、私有保护节、分阶段记录流，以及重建可用 ELF 镜像所需的结构。

它与 Windows 版本属于同一产品家族，但不是 PE 格式的变体。Android 的识别条件、节布局、记录流和元数据规则单独说明。

## 内容导航

| 分区 | 内容 |
| --- | --- |
| [文件格式](file-format/README.md) | ELF 识别、私有节和两阶段记录流 |
| [数据变换](data-transforms/README.md) | 外层首部、模块配置、容器变换和压缩 |
| [恢复](restoration/README.md) | 记录分发、动态链接和 ELF 输出 |
| [元数据](metadata/README.md) | IL2CPP 方法令牌和元数据存储方式 |
| [分析](analysis/README.md) | 校验规则、失败处理和已观察常量 |

Windows PE 格式请参阅 [Windows internals Space](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt)。

本文档是研究参考，记录已观察到的结构和校验行为，不提供产品操作流程或通用解包步骤。
