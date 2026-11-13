---
description: "受保护 Android ELF64 共享库与 IL2CPP 元数据的分步失败即中止校验。"
icon: list-check
---

# 校验清单

每个候选 Android `.so` 共享库与 `global-metadata.dat` 都必须按顺序通过下列结构校验；任何硬性校验未通过都会立即中止还原，不会输出残缺文件。

{% stepper %}
{% step %}
## ELF 识别与 `SHT_LOUSER` 边界

* 校验文件为 ELF64、小端序、`EM_AARCH64`（`183`），满足 `e_phentsize == 0x38`、`e_shentsize == 0x40`，且 `.shstrtab` 为合法 UTF-8。
* 要求存在 `.dynsym`、`.dynstr`、`.gnu.version`、`.gnu.version_r`，以及至少一个符号哈希节（`.gnu.hash` 或 `.hash`）。还原流程还要求 `.dynamic`、`.rela.dyn` 和 `.rela.plt` 各自存在且唯一。
* 要求节头表末尾存在且仅存在一个 `SHT_LOUSER`（`0x80000000`）私有节，其起始位置紧接在已映射 `PT_LOAD` 文件区间末尾之后的 16 字节对齐边界处（中间若有对齐空隙须全零填充）。
{% endstep %}

{% step %}
## 第一阶段与第二阶段数据流提取

* 解码 `section_offset + outer_size` 处的 32 字节第一阶段头部，要求 `reserved == 0`、`size_copy == payload_size`、`payload_size > 0 && payload_size % 4 == 0`、`payload_offset >= 0x20`、`payload_offset + payload_size <= section_size - outer_size`、`entry_offset < payload_size` 且 `protect_size <= payload_size`。
* 解析第二阶段 `0x5C` 记录描述符表直至首个非零载荷偏移（表项数由 `dw0` 给出，上限 256），并在每个切片上校验 `id_copy == command_id` 及父数据流边界。
* 要求每个 Huffman/LZ 压缩块恰好读完全部压缩数据（`div_ceil(consumed_bits, 8) == src_len`）、输出长度精确匹配（`output_pos == out_len`）且 `pending == 0`。
* 要求包含必需模块 `0x9B`、`0x9D` 和 `0x9E`（若存在可选模块 `0x96`、`0x98` 和 `0x0C` 则一并使用）。对 SHA-256 摘要完全一致的重复模块去重，若同一模块 ID 出现摘要冲突则直接拒绝。
{% endstep %}

{% step %}
## 动态表重建与 ELF 输出

* 校验 `0x9E` 隐藏符号索引（`0 < target_index < symbol_count` 且互不重复）及 `.dynstr` 边界；剥离保护壳追加的末尾符号（`dlerror`、`__stack_chk_guard`、`__stack_chk_fail`），在 `0x96` 存在时逆置换辅助符号索引，识别并补齐 `libc` PLT 空洞，将已定义符号重定位规范化为有序的 `R_AARCH64_RELATIVE` 前缀（更新 `DT_RELACOUNT`），并在 `0x98` 存在时执行构造函数恢复。
* 将重建后的各表放入 `.dynsym` 之后的空闲窗口或新追加的 `PF_R` `PT_LOAD` 段，移除 `SHT_LOUSER`，将 `e_entry` 清零，把非 `SHF_ALLOC` 节重定位到可加载段之后，原子写入输出文件并从磁盘重新解析。
* 执行写入后硬性校验（解析合法性、`PT_LOAD` 文件边界、`.shstrtab`、不含 `SHT_LOUSER`、`e_entry == 0`，以及 `.dynsym` / `.rela.dyn` / `.rela.plt` 条目数精确匹配），并记录跨表链接器诊断信息。
{% endstep %}

{% step %}
## IL2CPP 元数据校验

* 要求文件带有魔数 `0xFAB11BAF`，且表布局通过版本校验：支持版本 `24`（`v24.1`，需与同一应用的模块 `0x0C` 配对）、`29`、`31`（带种子的五轮逆置换，含按表顺序重映射的 `-GMD` 回退）或 `39`（12 字节紧凑节目录）。
* 对未混淆或已还原的元数据保持原样不变（保证幂等），并在还原后校验每个镜像内方法区间连续不重叠，且 `0x06000000 | rid` 局部序号或 `0..active_count` 索引完整连续、无越界。
{% endstep %}
{% endstepper %}
