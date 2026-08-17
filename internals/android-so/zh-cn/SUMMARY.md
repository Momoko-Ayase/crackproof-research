# Table of contents

* [CrackProof for Android SO 内部机制](README.md)

* [文件格式](file-format.md)
    * [概览](file-format/README.md)
    * [受保护 ELF](file-format/protected-elf.md)
    * [第一阶段首部](file-format/stage1.md)
    * [第二阶段记录流](file-format/stage2-streams.md)

* [数据变换](data-transforms.md)
    * [概览](data-transforms/README.md)
    * [模块配置](data-transforms/module-config.md)
    * [容器变换](data-transforms/container.md)
    * [Huffman 与 LZ 压缩](data-transforms/compression.md)

* [恢复](restoration.md)
    * [概览](restoration/README.md)
    * [模块记录流](restoration/module-streams.md)
    * [动态链接](restoration/dynamic-linking.md)
    * [ELF 输出](restoration/elf-output.md)

* [元数据](metadata.md)
    * [概览](metadata/README.md)
    * [方法令牌](metadata/method-tokens.md)
    * [存储布局](metadata/storage-layouts.md)

* [分析](analysis.md)
    * [概览](analysis/README.md)
    * [校验清单](analysis/validation.md)
    * [常量](analysis/constants.md)
