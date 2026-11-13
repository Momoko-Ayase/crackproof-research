---
description: "复现已知 CrackProof 布局族的源码级 Windows PE 加壳工具。"
icon: shield-halved
---

# Arare

Arare 是从源码完整构建的 Windows PE 加壳器。它自行编译原生与托管加载器，并在每次加壳时独立生成密钥、AES 轮密钥表、字节码程序、Huffman/LZ 压缩表与各阶段元数据，不依赖任何商业样本或提取的存根模板。

原生加壳覆盖 x86 与 x64 的 EXE 和 DLL，支持四种结构布局族（`pe32`、`pe64-classic`、`pe64-modern` 与 `legacy-dll`）。托管加壳通过生成的 ECMA-335 启动类型与独立的原生解码器封装 IL 程序集。加壳产物已通过未修改版 Senbei 1.3.1 的静态脱壳验证，并在 Windows 11 build 26100（面向 Windows 10 与 Windows 11 构建）上完成了原程序、加壳产物与脱壳产物的实际运行验证。

内嵌运行时提供按构建派生目录名的 `%TEMP%` 门控调试日志、手动映射辅助 DLL 内的可配置环境检查、基于页异常（`KiUserExceptionDispatcher`）按需解密的页面加密、基于种子的加载器代码变形，以及启动完成后的元数据擦除。环境检查未通过时，若调试日志已开启，会先写入 `AAA-BBB-CCC` 结束码；原生 EXE 默认开启 `--antidebug-av=on`，在退出前先触发 `EXCEPTION_ACCESS_VIOLATION` 使附加的调试器中断，而 DLL、显式设为 `--antidebug-av=off` 的原生 EXE 与托管模块则直接调用 `TerminateProcess`。

底层格式规范详见 [CrackProof Windows 内部机制](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/)，静态脱壳工具详见 [Senbei](https://app.gitbook.com/s/tMIkyJzuS8q10cZToDDD/)。

## 本节目录

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-terminal"></i></td><td><strong>命令行用法</strong></td><td>CLI 的 <code>protect</code>、<code>inspect</code> 与 <code>verify</code> 命令、布局配置、环境检查、页面加密与调试日志。</td><td><a href="usage.md">命令行用法</a></td></tr><tr><td><i class="fa-window-maximize"></i></td><td><strong>桌面 GUI</strong></td><td>用于批处理任务队列、逐行覆盖布局与检查项、导出 PowerShell 脚本及结果校验的 WPF 前端。</td><td><a href="gui.md">桌面 GUI</a></td></tr><tr><td><i class="fa-circle-check"></i></td><td><strong>支持范围</strong></td><td>支持的原生与托管模块类型、已验证的 CLR 宿主、加壳期拒收条件及结构上限。</td><td><a href="support.md">支持范围</a></td></tr><tr><td><i class="fa-diagram-project"></i></td><td><strong>架构设计</strong></td><td>各 crate 边界、单副本节与资源编码、三阶段运行时启动流程，以及与商业版的已知差异。</td><td><a href="design.md">架构设计</a></td></tr><tr><td><i class="fa-hammer"></i></td><td><strong>开发指南</strong></td><td>编译原生加载器与托管工具、运行 Senbei 1.3.1 基准测试，以及工作区规范。</td><td><a href="development.md">开发指南</a></td></tr></tbody></table>

## 范围与许可证

Android 目标、独立的 IL2CPP `global-metadata.dat` 混淆，以及 `protect` 中的内核驱动选项不在支持范围内（实验性内核驱动项目单独位于 `kernel/` 目录下）。

{% hint style="info" %}
**许可证划分。** 宿主机工具链（`arare-cli`、`arare-engine`、`tools/managed`、`gui` 与 `verification/senbei-oracle`）采用 `AGPL-3.0-only`。PE 解析器（`arare-pe`）、编解码库（`arare-codec`）以及所有内嵌原生与托管运行时代码（`arare-runtime`、`runtime/`）均采用 `MIT`，因此受保护的输出文件中不会嵌入任何 AGPL 代码。
{% endhint %}
