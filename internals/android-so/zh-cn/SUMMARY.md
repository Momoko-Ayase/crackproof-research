# Table of contents

* [CrackProof for Android SO 内部机制](README.md)

## 文件格式 <a href="#file-format" id="file-format"></a>

* [概览](file-format/README.md)
* [受保护 ELF](file-format/protected-elf.md)
* [第一阶段首部](file-format/stage1.md)
* [第二阶段记录流](file-format/stage2-streams.md)

## 数据变换 <a href="#data-transforms" id="data-transforms"></a>

* [概览](data-transforms/README.md)
* [词、流与记录密码](data-transforms/word-and-record.md)
* [模块配置](data-transforms/module-config.md)
* [容器变换](data-transforms/container.md)
* [Huffman 与 LZ 压缩](data-transforms/compression.md)

## 恢复 <a href="#restoration" id="restoration"></a>

* [概览](restoration/README.md)
* [模块记录流](restoration/module-streams.md)
* [动态链接](restoration/dynamic-linking.md)
* [ELF 输出](restoration/elf-output.md)

## 运行时 <a href="#runtime" id="runtime"></a>

* [概览](runtime/README.md)
* [第一阶段引导](runtime/stage1-bootstrap.md)
* [第二阶段解释器](runtime/stage2-interpreter.md)
* [环境与完整性检查](runtime/environment-checks.md)
* [运行时模块](runtime/modules.md)

## 元数据 <a href="#metadata" id="metadata"></a>

* [概览](metadata/README.md)
* [方法令牌](metadata/method-tokens.md)
* [存储布局](metadata/storage-layouts.md)

## 分析 <a href="#analysis" id="analysis"></a>

* [概览](analysis/README.md)
* [校验清单](analysis/validation.md)
* [常量](analysis/constants.md)
