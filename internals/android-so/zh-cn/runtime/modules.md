---
description: "流解释器、ELF 与元数据恢复及运行时检查所使用的第二阶段模块标识目录。"
icon: layer-group
---

# 运行时模块

第二阶段记录通过 1 字节 `command_id`（`0x00`..`0xFF`）在模块表中注册各模块。静态恢复只需用到[模块流](../restoration/module-streams.md)中列出的模块；其余模块用于加载期环境检查或辅助功能。

## 流解释器与引导槽位

| ID | 职责 |
| --- | --- |
| `0xE2`..`0xE8` | 嵌套记录流解释器（`0xE2` 即解密后的第二阶段根映像） |
| `0xF3`..`0xF8` | 作为输入传给 `0xE3`..`0xE8` 的直接流切片（`sid = command_id - 0x10`） |
| `0xD0` | 第二阶段根据 `(X6, X7)` 登记的 `SHT_LOUSER` 文件尾映射 |

## 映像、符号、构造函数与元数据恢复

| ID | 职责 |
| --- | --- |
| `0x9B` | 恢复协调模块，持有 `Module9bConfig`（`header_seed`、`container_seed`、逆序 AES-256 轮密钥、`skip_aes`），负责还原目标段与内存页权限 |
| `0x9D` | 直接载荷模块，持有 `0x5C` 字节 `ProtectedDescriptor`、主 `PT_LOAD` 容器与辅助 ELF 容器 |
| `0x9E` | 从可见 ELF 中剥离的隐藏 `.dynsym` 符号项与 `.dynstr` 字符串 |
| `0x96` | 16 字节分组解密模块，持有 `auxiliary_symbol_seed`，用于还原辅助重定位表中的符号下标轮换 |
| `0x98` | 最终构造函数分发模块：映像还原完毕后解析并调用目标共享库的 `.init_array` 回调（对应 Windows 状态码 `280`） |
| `0x0C` | 仅限 IL2CPP 构建：hook `mmap` 以在加载时反混淆 `global-metadata.dat`，同时内嵌 `v24.1` 的 `methodIndex` 置换种子与 256 项例外表 |
| `0xB9` | 元数据相关的辅助数据块（IL2CPP 构建中带有实际内容；普通原生共享库中缺失或为空） |

## 环境探测、符号解析与完整性辅助模块

| ID | 职责 |
| --- | --- |
| `0x81` | 解密库名与符号名，通过 `dlopen` / `dlsym` 解析函数指针并缓存结果 |
| `0x8F` | 读取 `/proc/self/cmdline`，查询 `uid`/`gid`/`tid`，维护环境令牌，并检查路径属主与权限模式 |
| `0x97` | 扫描 `/proc` 下相同 UID 的进程，在写入代码前后切换 `mprotect` 权限，并启动分离式监控线程 |
| `0x02` | 发送 UDP 123 端口 NTP 时间查询，并将响应结果与阈值比较 |
| `0x69` | `fork` 探测子进程并检查其退出状态 |
| `0x60` | 扫描系统库目录、`/proc` 环境变量与运行时路径 |
| `0x40` | 校验 `base.apk` 与各 split APK 签名（依次检查 v3.1 -> v3 -> v2 -> v1/JAR） |
| `0x20` | 校验目标文件路径、ELF 头、`/proc/self/maps` 以及 `libc` 映射 |
| `0x33` | 构造 `dex2oat` 选项列表，并清理不匹配的 oat/art 产物 |
| `0x72` | 创建并监听 Unix 域套接字以接收连接（`bind` / `listen` / `accept`） |
| `0xB0` | 变换内部哨兵表 |

<details>
<summary>其他已观察到但尚未归类的模块 ID</summary>

`0x8E`、`0x6A`、`0x68`、`0x54`、`0x71`、`0x53`、`0xA4`、`0x58`、`0x73`、`0xA0`、`0xB2`。

这些标识与上述模块一同出现在嵌套的第二阶段记录流中，会登记到 256 槽模块表内，并在未置位 `flags & 0x100` 时正常执行 `init`/`entry` 回调。静态 ELF 恢复不依赖它们。
</details>
