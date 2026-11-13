---
description: "CrackProof 受保护 PE、Android 库与 IL2CPP 元数据的静态脱壳与检查工具。"
icon: screwdriver-wrench
---

# Senbei

Senbei（`1.4.0`）是面向 CrackProof 受保护二进制文件的静态脱壳与结构检查工具。它可直接从单个文件、Android 应用包及目录中还原并校验目标文件，全程无需运行目标程序或附加调试器。

Windows 与 Linux 原生发行版同时包含命令行工具 `senbei` 与桌面工作台 `senbei-gui`，内置英文、简体中文、繁体中文、日文和韩文界面。同一套核心引擎还提供 WebAssembly 构建版本，可在浏览器本地处理独立的 Windows PE 与元数据文件。

## 支持的输入类型

* **Windows PE（`PE32` 与 `PE32+`）：** 受保护的 `.exe` 和 `.dll` 模块（含原生模块与 .NET 托管程序集），以及外置 `.exe._`、`.dll._` 伴随载荷。
* **Android 原生库（`ELF64` AArch64）：** 独立的受保护 `.so` 文件，以及 `.apk`、`.apks`、`.xapk` 应用包。
* **Unity IL2CPP 元数据：** Windows `-GMD`（`v31`）布局，以及 Android 种子派生（`v24.1`、`v29`、`v31`、`v39`）或内嵌异或（`v24`）布局的 `global-metadata.dat` 文件。

底层容器格式与数据变换详见 [CrackProof Windows 内部机制](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/) 与 [CrackProof Android SO 内部机制](https://app.gitbook.com/s/Aoyn9wKiHAVzBKGSUifa/)。

## 本节目录

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-terminal"></i></td><td><strong>命令行用法</strong></td><td>CLI 命令（<code>unpack</code>、<code>inspect</code>、<code>--dry-run</code>、<code>--json</code>）、目录与安装包处理规则、显示语言、参数及退出码。</td><td><a href="usage.md">命令行用法</a></td></tr><tr><td><i class="fa-window-maximize"></i></td><td><strong>桌面 GUI</strong></td><td>原生桌面工作台（<code>senbei-gui</code>）：可视化批处理队列、详细分析视图、十六进制 + RVA 查看器、PE 对比与设置。</td><td><a href="gui.md">桌面 GUI</a></td></tr><tr><td><i class="fa-diagram-project"></i></td><td><strong>架构设计</strong></td><td>九个 crate 的工作区划分、分析报告与追踪架构、Windows 与 Android 还原流水线，以及 WASM 边界。</td><td><a href="design.md">架构设计</a></td></tr><tr><td><i class="fa-hammer"></i></td><td><strong>开发指南</strong></td><td>构建 CLI、桌面 GUI 与 WASM 目标，运行样本库、模糊测试与一致性测试，性能基准测试及环境变量。</td><td><a href="development.md">开发指南</a></td></tr></tbody></table>

## 各前端概览

| 前端 | 支持的目标 | 输出与报告 |
| --- | --- | --- |
| `senbei`（CLI） | 独立文件、文件夹、`.apk`/`.apks`/`.xapk` | 还原后的文件、运行日志、彩色终端输出、`--json` v1 报告 |
| `senbei-gui`（桌面端） | 独立文件、文件夹、`.apk`/`.apks`/`.xapk` | 还原后的文件，交互式 **概览** / **详细分析** / **十六进制** / **对比** / **条目** / **日志** 视图，JSON 与文本报告导出 |
| 浏览器端（`web/`） | 独立 Windows PE 文件（含 `._` 伴随文件）与 `global-metadata.dat` | 浏览器本地下载与 `Export JSON` 报告（输入文件全程留在本地设备） |
