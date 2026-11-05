---
description: "工作区布局以及 Windows 与 Android 恢复流水线。"
---

# 设计

本页介绍 Senbei 的工作区布局，以及 Windows 与 Android 恢复流水线。

## crate 布局

工作区由七个 crate 组成；浏览器绑定 `senbei-wasm` 是工作区之外的独立 crate。

* `senbei-cli` 是命令行入口。
* `senbei-io` 负责文件系统编排。
* `senbei-pe` 提供基础格式解析。
* `senbei-elf` 提供基础格式解析。
* `senbei-crypto` 提供共享原语。
* `senbei-metadata` 恢复元数据。
* `senbei-engine` 负责保护方案专属的流水线。

单一平台的源码直接放在 `src/` 下。多平台 crate 把平台代码放在 `src/windows/` 与 `src/android/` 下，共享代码直接放在 `src/` 下。

```text
senbei-cli/src/main.rs
senbei-crypto/src/
senbei-crypto/src/android/
senbei-crypto/src/windows/
senbei-elf/src/
senbei-engine/src/windows/
senbei-engine/src/android/
senbei-io/src/
senbei-io/src/android/
senbei-io/src/windows/
senbei-metadata/src/
senbei-metadata/src/windows/
senbei-metadata/src/android/
senbei-pe/src/
senbei-wasm/src/
```

`senbei-pe` 与 `senbei-elf` 负责经过验证的格式模型、地址映射与 ELF 动态哈希辅助。它们不依赖解包引擎、文件系统代码或平台保护逻辑。

## 保护 profile

开发树中的共享模型 `senbei-engine/src/profile.rs` 记录观察到的格式、保护证据、候选尝试、选中流程、恢复状态与最终静态验证状态。其 `format_version` 表示报告格式版本，不是保护器构建版本。检测不会替代试解再验证，也不会根据未经验证的指纹指定 CrackProof 版本。

检查模式让恢复与验证保持未尝试状态。恢复报告保留被拒绝候选及其错误，即使后续流程成功也不会丢弃。伴生文件准备可以在候选运行前阻止恢复；覆盖恢复后的验证描述实际返回的映像，而不是早先的候选。静态验证不表示 Windows 或 Android 链接器已成功加载该映像。

元数据布局定义位于 `senbei-metadata/src/layout.rs`，与恢复算法分离。头部识别报告原始版本与已实现的能力。`known` 表示存在布局定义，不表示输入的表已经通过验证。版本 24 仍需要所属应用的模块 `0x0C` 与布局验证；仅凭原始版本不能识别 v24.1。带种子方法令牌恢复支持现有的 v29、v31 与紧凑 v39 流程，结构化恢复仍仅支持 v31。未知版本保留数值标记，但不声称支持恢复。

## Windows 引擎

`senbei-engine/src/windows/` 包含 PE 检测、布局发现、EXE 与 DLL 恢复、确定性块并行以及结构完整性检查。候选布局先经过试解再验证，然后才会被接受为输出。

外置伴生输入重建为 `stub[..4096]` 后接匹配的 `._` 载荷。stub 的导出、TLS 与声明的 CLR 区域在解包后覆盖回去，因为这些区域不存在于加密的伴生文件中。托管恢复沿 COR20 目录以及被引用的元数据、资源、vtable 修复表，按各文件的 RVA 映射进行，保留解密出的方法体。

## Android 引擎

`senbei-engine/src/android/extract/` 解密 stage-1 头部与 stage-2 记录流，并写出临时模块工作区。`senbei-engine/src/android/restore/` 把解码后的映像与修复容器应用到被掏空的 ELF 上，并重建动态链接器表。两个阶段在写输出前都验证边界与表放置。

Windows 保护原语在 `senbei-crypto/src/windows/`，Android 保护原语在 `senbei-crypto/src/android/`。Android 带种子元数据恢复在 `senbei-metadata/src/android/`；结构化的 MethodDef 变换共享在 metadata crate 根部，因为两个平台路径都使用它。

Android ELF 动态表根据输入节表及其实际文件范围定位。原始间隙太小时，恢复会在现有加载映像之后新增一个经过验证的只读 `PT_LOAD` 并更新动态标记；它绝不覆盖相邻节，也不发出不完整映像。

## 扫描与包

文件夹扫描使用平台目标名来避免打开批量资产：Windows 候选名为 `.exe`、`.dll` 与 `global-metadata.dat`；Android 候选名为 `.so` 与 `global-metadata.dat`。共享遍历器在 `senbei-io/src/scan.rs`；平台名称过滤与 PE 伴生字节适配在 `senbei-io/src/windows/`，Android 包适配在 `senbei-io/src/android/`。Windows 的 `.exe._`、`.dll._` 伴生文件是其同级 stub 的辅助输入，不计入跳过数。

APK、APKS、XAPK 文件是容器。Senbei 先读取它们的 ZIP 清单，必要时跟进嵌套 APK 条目，只提取 `.so` 与精确匹配 `global-metadata.dat` 的条目。提取直接流式写到临时文件，压缩副本与解压副本不会同时驻留内存。

## 验证

每个启发式布局都使用试解再验证。未通过结构检查、校验和或表边界的候选会被拒绝，然后尝试下一个候选。恢复失败会报告为错误，而不是发出静默损坏的二进制文件。

PE 完整性检查验证头部、节范围、入口点映射、导入名、重定位需求与托管元数据签名。Android 恢复验证 ELF 范围、解码后的容器大小、修复表边界与重建的动态表。

## WebAssembly

浏览器绑定通过 I/O 字节 API 依赖 `senbei-engine`。原生文件系统与 Android 包编排不在浏览器版工作流内。每次浏览器版解包都在一次性 worker 中运行，因为 WebAssembly 无法像原生代码那样从捕获的 panic 中恢复。
