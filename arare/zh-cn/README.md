---
description: "源码生成的 Windows PE 保护器，复现已观察到的 CrackProof 布局族。"
---

# Arare

Arare 是源码生成的 Windows PE 保护器。它自行生成加载器、密钥、AES 日程、字节程序、压缩表与阶段元数据。没有商用供体可执行文件，也没有抽出的 stub 配置。

原生保护覆盖 x86 EXE/DLL 与 x64 EXE/DLL，对应 PE32、经典 PE32+、现代 PE32+ 与遗留 DLL 族。托管保护使用可读的 IL 入口包装与独立的原生解码器。兼容性对照未改动的 Senbei 检查，并通过执行生成的原始、受保护与恢复后的程序验证。不以商用字节一致为目标。

目标平台是 Windows 10 与 Windows 11。当前执行证据来自 Windows 11 内部版本 26100。运行时行为跟随已观察的 CrackProof 流水线：按构建门控的调试日志（使用原始状态码）、可配置的环境与反分析检查（由手动映射的支持模块运行）、按需解密的页加密、由种子决定的加载器代码变化，以及用尽后的运行时元数据擦除。检查失败时以 `AAA-BBB-CCC` 失败码静默结束。

这些输出所对应的保护格式与运行时行为记录在 [CrackProof Windows 内部机制](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/)。本项目的静态解包器 Senbei 记录在 [Senbei](https://app.gitbook.com/s/tMIkyJzuS8q10cZToDDD/)。

Android、作为打包选项的内核组件，以及独立的 IL2CPP 元数据混淆均延后。源码树中有实验性内核提供程序；它不是 `protect` 选项。

## 本节内容

| 页面 | 内容 |
| --- | --- |
| [用法](usage.md) | 命令行保护、检查与验证 |
| [图形界面](gui.md) | 生成相同命令行的 WPF 前端 |
| [支持范围](support.md) | 已测试族、主机与明确拒绝项 |
| [设计](design.md) | 工作区布局、编码与运行时约定 |
| [开发](development.md) | 构建、测试与贡献 |

## 许可证

命令行、格式编排与托管元数据写入器为 AGPL-3.0-only。PE 模型、编解码实现，以及独立编写的原生与托管运行时为 MIT。AGPL 元数据写入器不会嵌入受保护应用程序。Senbei 是只读测试参考，不进入普通工作区构建。
