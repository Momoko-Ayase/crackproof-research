---
description: "支持的 PE 与 CLR 输入矩阵、加壳期拒收条件、结构上限与运行时加载规则。"
icon: circle-check
---

# 支持范围

Arare 面向 Windows 10 与 Windows 11 构建，已在 Windows 11 build 26100 上使用源码编译的 x86/WOW64 与 x64 原生及托管程序完成实际运行验证（尚未单独在 Windows 10 环境下运行完整测试套件）。托管程序运行验证覆盖 .NET Framework 4.8（x86/x64）、CoreCLR 10.0.12（x64）与 Mono 6.13（x86）。

## 支持的输入矩阵

| 输入类型 | 内嵌存储配置 | 伴随文件（`._`）配置 |
| --- | --- | --- |
| 原生 x86 EXE 或 DLL | `pe32` | `pe32` |
| 原生 x64 EXE 或 DLL | `pe64-classic`, `pe64-modern` | `pe64-classic`（DLL 要求非零入口点）, `pe64-modern` |
| 原生 x64 DLL（专用布局） | `legacy-dll` | 不支持 |
| 纯 IL x86 或 AnyCPU DLL | `pe32` | `pe32` |
| 受支持的纯 IL x86 或 AnyCPU C# EXE | `pe32` | `pe32` |
| 纯 IL x64 DLL | `legacy-dll`, `pe64-classic`, `pe64-modern` | `pe64-classic`, `pe64-modern` |
| 纯 IL x64 EXE | `pe64-classic`, `pe64-modern` | `pe64-classic`, `pe64-modern` |
| 清除了 `COR20` `ILONLY` 标志的纯 IL DLL | 与对应位宽的纯 IL DLL 相同 | 与对应位宽的纯 IL DLL 相同 |

原生 IL2CPP 二进制文件（`GameAssembly.dll` 与宿主 EXE）按普通原生 PE 加壳；独立的 `global-metadata.dat` 混淆不在 Arare 的处理范围内。

## 加壳期拒收条件

输入文件若命中以下任一情况，`arare protect` 会在加壳时直接拒绝：

### 原生与通用 PE 限制

* **零入口点的经典伴随 DLL：** `AddressOfEntryPoint` 为 0 的 `pe64-classic` 伴随模式 DLL（无入口点 DLL 请改用内嵌存储或 `pe64-modern`）。
* **伴随模式 TLS 区间重叠：** x64 伴随模式下，TLS 条目区间与加载器保留的物理数据区发生重叠。
* **页面加密对齐与权限冲突：** 启用页面加密时存在可写可执行（`RWX`）节、`SectionAlignment < 0x1000`，或可执行节的 `VirtualAddress` 未按 `0x1000` 对齐。
* **纯绑定导入：** 原生导入描述符的 `OriginalFirstThunk == 0`，且映像内不含 hint/name RVA 或 VA。
* **PE32 EXE 导入表改写限制：** 需要改写节名或节权限才能让静态脱壳工具还原导入表的原生 PE32 EXE。
* **启用 XFG 的代码导出：** 同时带有代码导出与 `IMAGE_GUARD_XFG_ENABLED` 标志的原生模块。
* **映像与头部体积上限：** 计入新增 Arare 节后的总映像大小超过 `1 GiB`、节数量超过 `96`，或节表头部超过 `0x1000` 字节（`pe64-*` / `legacy-dll`）或 `0x400` 字节（`pe32`）。

### 托管程序集限制

* 真正的 C++/CLI 混合模式代码、原生 CLR 入口点或 vtable 修正表、ReadyToRun/AOT 映像，或非 IL 方法体。
* 强名称签名或延迟签名程序集、多模块程序集、链接/导出模块表、内嵌 Portable PDB，或编号 `>= 45` 的 CLI 元数据表（例如 `/debug:embedded`）。
* 清除了 `ILONLY` 标志的 x86 托管 EXE、置位了 `32BITREQUIRED` 或 `32BITPREFERRED` 的 PE32+ 托管输入、RVA 页面 `[0x1000, 0x2000)` 已被占用的 `pe64-modern` 零导入程序集，或导入目录非零但首项导入描述符为空的 `pe64-modern` 托管输入。
* 原生导出表、原生异常/展开目录或 TLS 目录、加载配置表（Load Config）、延迟导入、`VirtualSize > SizeOfRawData` 的节、Edit-and-Continue 或指针元数据表、CLI `vararg` 可变参数方法，或位于保留命名空间 `Arare.Managed` 内的类型。
* 元数据扩展新增的泛型填充 `TypeDef` 行数超过 `524,288`，或签名返回类型的嵌套层数超过 `128`、类型元素总数超过 `65,536`。

## 布局与运行时加载说明

* **位于可执行节内的数据导出：** PE 导出表本身不区分代码导出与数据导出，因此指向可执行节的非转发器导出项会被重定向到代码导出保护 thunk，而不会在加壳期拒收。导出的纯数据符号请放在不可执行的数据节中。
* **字节数组加载与磁盘加载：** 采用伴随文件模式加壳的托管程序集必须从磁盘文件加载，不支持 `Assembly.Load(byte[])`。清除了 `ILONLY` 标志的纯 IL DLL 遵循标准 CLR 混合模式加载规则：在 .NET Framework 与 CoreCLR 上需由位宽匹配的进程从磁盘加载，Mono 则同时支持磁盘加载和字节数组加载。
