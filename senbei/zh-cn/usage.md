---
description: "命令行用法：文件、包与文件夹目标，标志与退出码。"
---

# 用法

```text
senbei <file|folder> [--out DIR] [-v|--verbose] [-q|--quiet]... [--scan-all] [--strict-integrity] [--max-entry-mib N] [--max-total-mib N] [--max-entries N] [--max-depth N] [--no-log] [--no-pause] [-V|--version] [-h|--help]
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

`Companion missing?` 表示 Senbei 识别到明确声明 `._` 后缀的 PE32+ 加载器入口记录，但未提供伴生文件。把 `<input>._` 放在输入文件旁边，保留完整文件名（例如 `module.dll._`），或在浏览器中同时添加两个文件。此检查会验证 PE 结构、保护签名与入口记录，但不能证明 stub 的每个部分均完好。仅文件较小、节被清空或解包失败不会触发此提示。入口记录损坏或无法识别时，保留原始解包错误。

若已提供的伴生文件不足以容纳 32 字节配对头部，或头部与已识别加载器中的内容不同，Senbei 会报告 `Companion doesn't match`。请使用同一构建中的两个文件；任一文件都有可能损坏。伴生文件无法读取时报告文件读取错误。头部匹配但后续解密失败时，保留原始解包错误。

汇总行形如 `12 unpacked · 3 skipped · 0 errors · 1 suspect · 2 metadata`；打开过包时追加包计数。每个文件相互隔离，单个目标失败不会中断文件夹运行。

## 完整性检查

PE 输出会检查有效头部、节范围、入口点映射、可读导入名、重定位需求与托管元数据签名。Android 输出在 ELF 恢复过程中验证，包括解码后的容器大小、修复表边界与重建的动态表。

干净的报告不是正确性证明，但未通过的报告可以可靠地说明输出已损坏。可疑 PE 文件仍会写出并单独计数。`--strict-integrity` 不改变这一写出行为，只改变进程退出码。

## 标志

| 标志 | 行为 |
| --- | --- |
| `--out DIR` | 把输出与日志写到 `DIR` 下。 |
| `-v`, `--verbose` | 打印各阶段进度。 |
| `-q`, `--quiet` | 隐藏进度与逐文件行；重复使用可抑制全部标准输出。 |
| `--no-log` | 不写运行日志。 |
| `--scan-all` | 探测每个选定的目标名候选，包括低于大小下限的文件。 |
| `--strict-integrity` | 尚未进入已发布构建。任一输出未通过静态完整性检查（可疑）或任一文件出错时，以非零状态退出。默认关闭：可疑输出仍会写出，并且除非有文件出错，进程以 `0` 退出。重复 `-q` 的行为不变。 |
| `--max-entry-mib N` | 尚未进入已发布构建。仅用于 Android。正数 MiB 上限，约束解压过程中的单个 ZIP 条目、单个解码缓冲区、单次工件读取与单个输出文件。默认 `2048`（1 MiB = 1,048,576 字节）。 |
| `--max-total-mib N` | 尚未进入已发布构建。仅用于 Android。正数 MiB 上限，约束文件夹内累计的归档字节，以及单个引擎任务中另行记账的提取与恢复工作。默认 `8192`。这不是进程内存峰值上限。 |
| `--max-entries N` | 尚未进入已发布构建。仅用于 Android。正数上限，约束归档条目与 stage-2 记录，并跨嵌套归档计数。默认 `100000`。 |
| `--max-depth N` | 尚未进入已发布构建。仅用于 Android。嵌套 APK 与 stage-2 流的嵌套深度上限。根的深度为 `0`，允许传入 `0`。默认 `32`。 |
| `--no-pause` | 关闭便于资源管理器双击运行的 Windows 退出提示。 |
| `-V`, `--version` | 打印版本并退出。 |
| `-h`, `--help` | 显示用法。 |

## 退出码

| 代码 | 含义 |
| --- | --- |
| `0` | 请求的恢复已完成，没有错误。未设置 `--strict-integrity` 时，可疑输出仍以 `0` 退出。 |
| `1` | 目标失败、扫描探测不可读，或单文件恢复出错。加上尚未发布的 `--strict-integrity` 后，任一可疑输出也以 `1` 退出。输出仍会写出。超出 Android 资源上限时也以 `1` 退出；Senbei 不会静默截断这部分工作。 |
| `2` | 命令行无法解析。资源上限不是无符号十进制整数时属于命令行错误；除 `--max-depth` 外，传入 `0` 同样是命令行错误。 |
