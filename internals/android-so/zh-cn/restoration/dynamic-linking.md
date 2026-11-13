---
description: "重建动态符号表、符号哈希、重定位表、PLT 空洞、构造函数与 PT_LOAD 布局。"
icon: link
---

# 动态链接

从 `0x9D` 主容器还原出被挖空的 `PT_LOAD` 字节并写回 ELF 映像后，静态恢复流程会汇总 `0x9D`、`0x9E`、`0x96` 与 `0x98` 中的数据，重建被 CrackProof 剥离或拆分的动态链接表。

{% stepper %}
{% step %}
## 还原隐藏符号并剔除保护壳尾部导入

模块 `0x9E` 开头为 `{u32 blob_size, u32 secondary_record_count}`，接着在 `+0x08` 处存放 `{u32 count, u32 symbol_offset, u32 index_offset, u32 string_offset}`，随后依次是 `count` 个 24 字节 `Elf64_Sym` 表项、`count` 个 `u32` 目标 `.dynsym` 下标，以及以 NUL 结尾的符号名字符串（附带 0 至 3 字节零填充对齐）。每条回填记录的目标下标必须满足 `0 < target_index < symbol_count` 且互不重复，`st_name` 指向的字符串也必须落在 `.dynstr` 边界内（写入全零空隙，或与该偏移处原有的同名字符串完全一致）。

如果在 `0x9E` 最大的 `target_index` 之后，动态符号表尾部的剩余符号全部属于保护壳注入的导入集合 `{"dlerror", "__stack_chk_guard", "__stack_chk_fail"}`，则在追加辅助符号之前，先将这些尾部符号以及所有引用它们的重定位项一并移除。
{% endstep %}

{% step %}
## 追加辅助符号并还原重定位符号下标

`0x9D` 的辅助 ELF 容器提供 `relocation1`（`.rela.dyn` 候选表）、`relocation2`（`.rela.plt` 候选表）、辅助 `.dynsym`（下标 `0` 为空项，外加 `N - 1` 个外部符号）以及辅助 `.dynstr`。其中非空符号会追加到主 `.dynsym` 末尾（同步扩展 `.dynstr`，并在 `.gnu.version` 中为其填入 `VER_NDX_GLOBAL = 1`，而 `.gnu.version_r` 直接沿用已恢复主映像中的内容）。

当存在模块 `0x96`（且 `N > 1`）时，`relocation1` 与 `relocation2` 中的非零辅助符号下标（`1..N-1`）会基于 `0x96` 中的 32 位 `auxiliary_symbol_seed`，按重定位项序号 `row` 逐项轮换：

```text
s2       = (seed * seed) & 0xFFFFFFFF
left     = ((s2 >> (row & 0x1B)) + 0x1BC5) & 0xFFFFFFFF
right    = (((s2 << (row & 3)) & 0xFFFFFFFF) + 0x2048) & 0xFFFFFFFF
rotation = (left | right) % (N - 1)
```

先在模 `N - 1` 下还原该轮换偏移，再加上 `old_symbol_count - 1`，即可使每条重定位项的 `r_info` 指向合并后 `.dynsym` 中的正确槽位。
{% endstep %}

{% step %}
## 识别并补齐 `libc` PLT 空洞

CrackProof 最多会从 `relocation2` 中省略 5 个标准 `libc` 字符串与内存函数（`strlen`、`strcmp`、`memset`、`strcpy`、`strchr`），导致 `.got.plt`（跨过开头 `0x18` 字节头部后）留下无重定位引用的空洞槽位。恢复流程将每个空洞槽位映射回 `.plt + 0x20 + slot * 0x10`（同时识别编译器生成的 `ADRP X16/X17; ADD; BR` 跳板桩），扫描 `.text` 中各 AArch64 调用点的参数寄存器与返回值用法来判定具体函数，随后向符号表追加 `SHN_UNDEF` 的 `STT_FUNC` 符号，并向 `.rela.plt` 补入缺失的 `R_AARCH64_JUMP_SLOT`（`0x402`）重定位项。
{% endstep %}

{% step %}
## 规范化 `.rela.dyn`、重建符号哈希与恢复构造函数

在 `.rela.dyn` 中，凡是目标符号已定义（`st_shndx != SHN_UNDEF`）的 `R_AARCH64_ABS64`（`0x101`）或 `R_AARCH64_GLOB_DAT`（`0x401`）记录，统一转换为 `R_AARCH64_RELATIVE`（`0x403`），并令 `r_addend = st_value + r_addend`。所有 `R_AARCH64_RELATIVE` 表项按 `r_offset` 升序排列在 `.rela.dyn` 最前面，同时将 `DT_RELACOUNT` 更新为该前缀长度。

输入 ELF 原本携带的符号哈希节（`.gnu.hash`、SysV `.hash` 或二者兼有）均基于最终 `.dynsym` 完整重建。当存在模块 `0x98` 时，有界 AArch64 解释器从 `entry_offset` 开始执行（令 `X0 = runtime`、`[X0 + 8] = image_base`，并校验执行至 `RET` 时 `W0 == 1`），还原被隐藏的构造函数：替换 `.init_array` 中的第一阶段引导槽位，剔除仅含单条 `RET`（`0xD65F03C0`）的占位桩，并同步更新 `.init_array` / `.fini_array` 的节大小以及 `DT_INIT_ARRAYSZ` / `DT_FINI_ARRAYSZ`。
{% endstep %}

{% step %}
## 原地写回或追加只读 `PF_R` `PT_LOAD` 段存放动态表

若重建后的 `.dynsym`、`.gnu.version`、哈希表、`.dynstr`、`.rela.dyn` 与 `.rela.plt` 能够完整放进从 `.dynsym` 起算的原始文件窗口，则直接原地写回。当扩展后的表总长度超出原有窗口时，恢复流程会在文件末尾按现有 `PT_LOAD` 段的最大 `p_align` 对齐，追加一个新的只读（`PF_R`）`PT_LOAD` 段，并同步更新 `DT_SYMTAB`、`DT_STRTAB`、`DT_STRSZ`、`DT_GNU_HASH` / `DT_HASH`、`DT_VERSYM`、`DT_RELA`、`DT_RELASZ`、`DT_JMPREL` 与 `DT_PLTRELSZ`。

为了在不覆盖已映射字节的前提下插入新增的 `Elf64_Phdr`，重建流程会优先利用程序头表末尾原有的对齐空隙；若无空隙但 `PT_LOAD` 内存在两个及以上 `PT_NOTE` 程序头，则复用其中冗余的 `PT_NOTE` 槽位；否则将整张程序头表迁移到新追加 `PT_LOAD` 段的开头，并同步更新 `e_phoff` 与 `PT_PHDR`。
{% endstep %}
{% endstepper %}
