---
description: "面向 CrackProof 保护的 Windows PE 文件与 Android AArch64 共享库的静态解包器。"
---

# Senbei

Senbei 是面向 CrackProof 保护程序的静态解包器。指向一个文件、应用包或文件夹，它会在不启动、不附加受保护程序的情况下写出恢复后的副本。

Senbei 读取受保护字节，静态重放保护算法，按结构检查验证结果，然后写出恢复后的映像。验证失败的候选结果会被拒绝，绝不会作为静默损坏的二进制文件发出。

支持的输入：

* 受保护的 Windows `.exe` 与 `.dll` 文件——64 位与 32 位、原生与托管——包括外置 `.exe._`、`.dll._` 伴生载荷
* 具有受支持方法令牌布局的 `global-metadata.dat` 文件
* 受保护的 Android `.so` 文件，可为独立文件，也可位于 `.apk`、`.apks`、`.xapk` 包内

这些输入背后的保护格式与运行时行为记录在 [CrackProof Windows 内部机制](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/)与 [CrackProof Android SO 内部机制](https://app.gitbook.com/s/Aoyn9wKiHAVzBKGSUifa/)。

## 本节内容

| 页面 | 内容 |
| --- | --- |
| [用法](usage.md) | 命令行工具的运行方式：目标、标志与退出码 |
| [设计](design.md) | 工作区与恢复流水线的组织方式 |
| [开发](development.md) | 构建、测试与贡献 |

## 浏览器应用

同一引擎也可编译为 WebAssembly 在浏览器中运行。文件在本地处理，不会上传。浏览器版本处理单个文件；文件夹扫描与 Android 包编排仍由命令行工具负责。
