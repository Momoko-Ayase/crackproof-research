---
description: "命令行用法：文件、包与文件夹目标，标志与退出码。"
---

# 用法

```text
senbei <file|folder> [--out DIR] [-v|--verbose] [-q|--quiet]... [--scan-all] [--no-log] [--no-pause] [-V|--version] [-h|--help]
```

## 单个文件

Senbei 把输出写到 `<parent>/unpack/` 下，并在扩展名前插入 `.unpack`。`--out DIR` 同时改变输出目录与日志目录。

```cmd
senbei app.exe
senbei app.exe --out C:\out
```

对于 `global-metadata.dat`，只有方法令牌发生变化时 Senbei 才写出 `global-metadata.unpack.dat`。不支持的元数据版本保持原样，并报告为跳过。

## Android 目标

Senbei 从加密载荷节恢复受保护的 `.so` 文件，写出为 `libil2cpp.unpack.so` 或对应的输入名。APK、APKS、XAPK 文件按容器处理：Senbei 先读取清单，必要时跟进嵌套 APK，只提取 `.so` 与精确匹配 `global-metadata.dat` 的条目。

如果恢复后的库包含内嵌元数据，Senbei 会把解包后的数据块作为 `global-metadata.unpack.dat` 写到它旁边。内容相同的松散文件与包内条目只恢复一次，优先取松散文件。

## 文件夹模式

文件夹模式递归遍历，跳过名为 `unpack` 的目录，并把识别到的输出按相对路径写到 `<root>/unpack/` 或 `--out DIR` 下。Windows 候选名为 `.exe`、`.dll` 与 `global-metadata.dat`；Android 候选名为 `.so` 与 `global-metadata.dat`。匹配的 `.exe._`、`.dll._` 载荷由其 stub 消费，不计入跳过数。

托管 DLL 伴生文件在原始 DLL 中保留 CLR 元数据及相关运行时表。DLL 与其匹配的 `._` 文件必须同时可用；Senbei 从 DLL 恢复声明的 CLR 区域，同时保留从伴生文件解密的方法体。被引用区域缺失或不可读时报告为错误。

汇总行形如 `12 unpacked · 3 skipped · 0 errors · 1 suspect · 2 metadata`；打开过包时追加包计数。每个文件相互隔离，单个目标失败不会中断文件夹运行。

## 完整性检查

PE 输出会检查有效头部、节范围、入口点映射、可读导入名、重定位需求与托管元数据签名。Android 输出在 ELF 恢复过程中验证，包括解码后的容器大小、修复表边界与重建的动态表。

干净的报告不是正确性证明，但未通过的报告可以可靠地说明输出已损坏。可疑 PE 文件仍会写出并单独计数。

## 标志

| 标志 | 行为 |
| --- | --- |
| `--out DIR` | 把输出与日志写到 `DIR` 下。 |
| `-v`, `--verbose` | 打印各阶段进度。 |
| `-q`, `--quiet` | 隐藏进度与逐文件行；重复使用可抑制全部标准输出。 |
| `--no-log` | 不写运行日志。 |
| `--scan-all` | 探测每个选定的目标名候选，包括低于大小下限的文件。 |
| `--no-pause` | 关闭便于资源管理器双击运行的 Windows 退出提示。 |
| `-V`, `--version` | 打印版本并退出。 |
| `-h`, `--help` | 显示用法。 |

## 退出码

| 代码 | 含义 |
| --- | --- |
| `0` | 请求的恢复已完成，没有错误。 |
| `1` | 目标失败、扫描探测不可读，或单文件恢复出错。 |
| `2` | 命令行无法解析。 |
