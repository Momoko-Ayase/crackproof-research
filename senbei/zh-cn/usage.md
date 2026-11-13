---
description: "CLI 命令、检查报告、目录与 Android 包处理、显示语言、命令行参数及退出码。"
icon: terminal
---

# 命令行用法

```text
senbei [inspect|unpack] <file|folder> [--out DIR] [-v|--verbose] [-q|--quiet]...
    [--json] [--dry-run] [--threads N] [--color auto|always|never] [--scan-all]
    [--strict-integrity] [--max-entry-mib N] [--max-total-mib N]
    [--max-entries N] [--max-depth N] [--no-log] [--no-pause]
    [-V|--version] [-h|--help]
```

`senbei <path>` 等价于 `senbei unpack <path>`。`inspect` 与 `unpack` 位于 `<file|folder>` 之前时会作为子命令解析；若要处理名为 `inspect` 的文件或文件夹，请传入 `./inspect` 或 `.\inspect`。

## 常用流程

{% tabs %}
{% tab title="脱壳" %}
还原后的文件默认写入 `<parent>/unpack/`（单文件输入）或 `<root>/unpack/`（文件夹输入），并在原扩展名前插入 `.unpack`；传入 `--out DIR` 可同时指定输出文件与运行日志的保存目录：

```cmd
senbei app.exe
senbei app.exe --out C:\out
senbei game.apk --out C:\out
senbei "C:\Games\SampleTitle"
```

处理 `global-metadata.dat` 时，仅当方法 token 或索引确实发生变更时才会写出 `global-metadata.unpack.dat`；已是标准格式或版本不受支持的文件在文件夹扫描中会直接跳过，单独指定为目标时则报错。
{% endtab %}

{% tab title="检查与 JSON" %}
`inspect` 在内存中执行完整的静态还原流程以收集详细分析数据，不写出还原文件或运行日志，也不会执行目标文件：

```cmd
senbei inspect module.dll
senbei inspect module.dll --json
senbei inspect module.dll --strict-integrity --json
```

报告内容包含源文件哈希、解析后的 PE/ELF/元数据头部、解码后的保护表、每条尝试过的还原路径及淘汰原因、最终选中的路径、识别出的各阶段参数（严格区分物理文件偏移、伴随文件拼接偏移与工作映像 RVA），以及静态校验结果。
{% endtab %}

{% tab title="试运行与 CI" %}
`--dry-run` 执行还原与静态校验，但不写出输出文件或日志，也不采集 `inspect` 的详细追踪数据。Android 解包产生的临时目录会在运行结束后自动清理：

```cmd
senbei unpack module.dll --dry-run
senbei unpack module.dll --dry-run --json --strict-integrity
senbei unpack folder --strict-integrity --no-pause -q
```

`inspect` 与 `--dry-run` 均不能同 `--out` 混用。
{% endtab %}
{% endtabs %}

## Android 原生库与安装包

Senbei 可还原受保护的 AArch64 `.so` 文件（输出为 `libil2cpp.unpack.so` 或 `<stem>.unpack.so`），并支持直接输入 `.apk`、`.apks` 与 `.xapk` 应用包：

1. 首先读取 ZIP 中央目录，并按 `--max-depth` 深度上限递归解析 `.apks`/`.xapk` 内的嵌套 `.apk` 条目。
2. 在 `--max-entry-mib`、`--max-total-mib` 与 `--max-entries` 配额内，仅将 `.so` 和文件名为 `global-metadata.dat` 的条目流式解出到临时文件。
3. 将外置 `v24.1` 元数据与所属应用的 `0x0C` 模块配对（跨 split APK 按 `AndroidManifest.xml` 的包名与版本匹配，目录模式下按 `<root>/lib/<abi>/` 与 `<root>/assets/` 匹配），将精简版 `v24` 异或数据块解包为 `global-metadata.unpack.dat`，并对内容相同的独立文件与包内文件自动去重。

## 文件夹扫描与伴随文件

文件夹模式会递归遍历子目录，自动跳过名为 `unpack` 的目录（不区分大小写，除非目标根目录本身名为 `unpack`），并跳过根目录下的 NTFS 重解析点子目录：

* **扫描文件名规则（不区分大小写）：** `.exe`、`.dll`、`.so`、`global-metadata.dat`、`.apk`、`.apks` 和 `.xapk`。共享同一清单包名与版本的同级 split `.apk` 会自动归为一组。未指定 `--scan-all`（或设置 `SENBEI_SCAN_ALL`）时，小于 `4,128` 字节的候选文件默认不打开，直接跳过。
* **Windows `._` 伴随文件：** 同目录下的 `.exe._` 与 `.dll._` 会由对应的主存根文件一并读取，不会计入已跳过文件。带伴随文件的托管 DLL 必须同时提供 `Module.dll` 和 `Module.dll._`，以便 Senbei 将存根中的 `COR20` 表补回包含解密后 IL 方法体的还原映像。

{% hint style="info" %}
**伴随文件诊断信息。** 仅当 PE32+ 入口记录明确带有 `._` 伴随文件声明（`~0x1000` 与 `~"._\0\0"`）且同目录下缺少 `<input>._` 时，才会报告 `Missing companion file`。若 `<input>._` 不足 32 字节，或其 `0x00..0x20` 头部与 `stub[0x1000..0x1020]` 不一致，则报告 `Companion doesn't match`。
{% endhint %}

## 显示语言与终端颜色

Senbei 支持五种显示语言：`en`（英文）、`zh-CN`（简体中文）、`zh-TW`（繁体中文）、`ja`（日文）和 `ko`（韩文）。

{% tabs %}
{% tab title="Command Prompt" %}
```cmd
set SENBEI_LANG=ja
senbei inspect module.dll
```
{% endtab %}

{% tab title="PowerShell" %}
```powershell
$env:SENBEI_LANG = "zh-TW"
senbei inspect module.dll
```
{% endtab %}

{% tab title="POSIX / Bash" %}
```sh
SENBEI_LANG=ko senbei inspect module.dll
```
{% endtab %}
{% endtabs %}

* **区域解析规则：** `SENBEI_LANG` 会先剥离 `.encoding` 和 `@modifier` 后缀，不区分大小写并兼容 `-` 与 `_` 分隔符，且文字子标签（`Hans` / `Hant`）优先于地区代码（`zh-Hans-HK` -> 简体中文；`zh-Hant`、`zh-TW`、`zh-HK`、`zh-MO` -> 繁体中文）。未设置 `SENBEI_LANG` 时，Senbei 依次读取 Windows UI 语言列表或 `LC_ALL` / `LC_MESSAGES` / `LANG` / `LANGUAGE`，均未命中则回退为英文。
* **固定保持英文的输出：** `--json` 报告、保存的 `.log` 日志文件、`inspect` 的结构化分析表格，以及 `-v` 的阶段明细始终保持英文；若本地化错误提示仅概括了错误类别，下一行会原样输出更具体的英文内部错误详情。
* **终端颜色（`--color MODE` 或 `--color=MODE`）：** 默认值 `auto` 会分别检测各输出流的 TTY 状态，并在 `NO_COLOR` 非空或 `TERM=dumb` 时关闭颜色；`always` 在终端文本输出中强制启用 ANSI 颜色；`never` 禁用颜色。`--json` 输出与 `.log` 日志不包含 ANSI 转义序列。

## 静态校验与浏览器端限制

静态校验会检查还原后的 PE 头部、节映射、入口点可达性与 CRT 分支目标、最多 256 项导入描述符、原生数据目录和 CLR `BSJB` 元数据流，以及 Android ELF 的 `PT_LOAD` 边界、动态表、符号哈希表、重定位项和构造函数指针。带有结构告警或非致命错误的输出在 `unpack` 模式下仍会正常写出并计为 `suspect`（可疑）；指定 `--strict-integrity` 后，只要出现 `suspect` 结果（无论在 `unpack`、`--dry-run` 还是 `inspect` 下），进程即返回退出码 `1`。

在 WebAssembly 浏览器端应用中，**Input limit per module (MiB)** 默认为 `256`（范围 `8`..`4096` MiB，在读入内存前合并计算主存根与 `._` 伴随文件的体积），点击 **Export JSON** 可在本地下载 `senbei.browser-report` v1 文件。Android `.so` 与应用包还原需使用原生版 `senbei` 或 `senbei-gui`。

## 参数参考

| 参数 | 行为说明 |
| --- | --- |
| `--out DIR` | 将还原后的文件与运行日志写入 `DIR`（仅限 `unpack` 模式）。 |
| `--dry-run` | 执行还原与校验，但不保存输出文件或日志。 |
| `--json` | 向 `stdout` 输出带版本号的 JSON 报告（即使指定了 `-q -q` 也会输出）；同时禁用运行日志与退出暂停。 |
| `--threads N` | 工作线程数上限（`N >= 1`），优先于 `SENBEI_THREADS`（设为 `1` 时串行执行）。 |
| `--color auto\|always\|never` | 控制终端 ANSI 颜色输出（也支持 `--color=MODE` 写法）。 |
| `-v`, `--verbose` | 打印各阶段的详细进度行。 |
| `-q`, `--quiet` | 隐藏横幅与单文件进度；分开传入两个 `-q`（即 `-q -q`）可关闭全部 `stdout` 及运行时 `stderr` 输出。 |
| `--no-log` | 不写入 `senbei-YYYYMMDD-HHMMSS.log` 日志文件。 |
| `--scan-all` | 文件夹扫描时一并探测小于 `4,128` 字节的候选目标文件。 |
| `--strict-integrity` | 只要有任意还原映像被标为 `suspect`，即返回退出码 `1`（适用于 `unpack`、`--dry-run` 与 `inspect`）。 |
| `--max-entry-mib N` | 单个 Android ZIP 条目、解码容器、中间产物或输出文件的大小上限，单位 MiB（`N >= 1`，默认 `2048`）。 |
| `--max-total-mib N` | Android 压缩包解包与单任务还原的累计数据量上限，单位 MiB（`N >= 1`，默认 `8192`；按累计处理体积计算，并非进程峰值内存上限）。 |
| `--max-entries N` | 嵌套 Android 压缩包条目数与 Stage 2 记录数的上限（`N >= 1`，默认 `100000`）。 |
| `--max-depth N` | 嵌套 Android APK 与 Stage 2 流的递归深度上限（允许为 `0`，默认 `32`）。 |
| `--no-pause` | 从 Windows 资源管理器双击启动时跳过退出前的按键提示。 |
| `-V`, `--version` / `-h`, `--help` | 打印版本号或命令行帮助并以退出码 `0` 结束。 |

## 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 命令成功完成（`unpack`、`--dry-run`、`inspect`、`--help` 或 `--version`），无任何目标报错（启用 `--strict-integrity` 时且无 `suspect` 输出）。 |
| `1` | 至少一个目标还原失败、目录扫描或文件探测无法读取、超出 Android 资源配额，或在 `--strict-integrity` 下遇到 `suspect` 映像。 |
| `2` | 命令行参数无效（包括未传任何参数直接运行 `senbei`、参数组合互斥，或数值限制非法）。 |
