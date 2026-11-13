---
description: "标准与紧凑 PE32 壳体、专用 64 位 DLL 及无标记 64 位构建的结构差异。"
icon: code-branch
---

# PE32、DLL 与无标记布局

{% tabs %}
{% tab title="PE32（标准与紧凑壳体）" %}
32 位（`0x10B`）容器运行八阶段加载链（`SecondStage` 至 `EighthStage`），内部偏移需加上随构建变化的阶段尺寸差值 `ss_shift`。已观测到的构建包含两种 `tbl` 布局（早期紧凑壳还可能在 `payload_xor_chain` 中加密整段 `info[5]` 载荷）：

| 结构 / 偏移项 | 标准 PE32（`match - 0x88`） | 紧凑 PE32（`match - 0x78`） |
| --- | --- | --- |
| `tbl` 内 `info[6]` 匹配位置 | `tbl + 0x88` | `tbl + 0x78` |
| 头部校验和描述符链 | `tbl + 0x58` | `tbl + 0x50` |
| `SecondStage` `(offset, size)` | `tbl + 0x98` | `tbl + 0x88` |
| `first_stage_cs` / `second_stage_cs` | `tbl + 0xA8` / `tbl + 0xB0` | `tbl + 0x98` / `tbl + 0xA0` |
| 保存的导入表 RVA | `tbl + 0xBC` | `tbl + 0xAC` |
| 保存的资源目录 `(RVA, size)` | `tbl + 0xC8` / `tbl + 0xCC` | `tbl + 0xB0` / `tbl + 0xB4` |
| 阶段尺寸差值 `ss_shift` | `ss_size - 0xBC0` | `ss_size - 0xAEC` |
| `SevenStage` 种子（`seven_key`） | `~u32@(cs1_addr + cs1_size - 0x10)` | `~u32@(cs1_addr + cs1_size - 0x0C)` |

紧凑 PE32 同时将 `SecondStage` 内部指针偏移调整为 `third_pair_off = 0xAB4 + ss_shift`，以及 `forth_key_off / third_key_off / cs_base_off / dp_base_off = 0x94C / 0x950 / 0x954 / 0x9C4 + ss_shift`。

* **头部校验和与 DLL `BaseReloc` 双路试探：** `header_checksum` 对加壳前的 PE 头部各区间逐段计算 `calculate_checksum` 并累积异或。原生 PE32 DLL 的外层头部带有加壳器填入的 `DD[5]`（`BaseReloc`）表项，而该项在加壳前原本为零；因此还原时需同时测试当前头部与清零 `DD[5]` 后的头部副本，保留能使 `ThirdStage` 通过校验的一组。
* **`ThirdStage` 移位量遍历：** 依次尝试 `[19, 21, 17, 23, 15, 25, 13, 11]`，直至解密结果出现信息表签名（`1`/`0x11` 后紧跟 `2` 及合法映像内地址）；四项 `key_offsets` 位于该位置前方 `0x58` 字节处。
* **动态 `advance_key` 轮数（`Fourth` / `Fifth` / `Seventh` / `Eighth`）：** PE32 不使用固定轮数，而是在 `dp_base` 与 `dp_base + 0x80` 两张四槽位表中统计起始处连续有效的 16 字节辅助描述符数量（满足 `size > 4`，遇到首个空槽即停止）。
* **`EighthStage` 密钥与配置簇定位：** 结合区间间隙特征与不可打印双字扫描收集 `EighthStage` 种子候选，并以 Huffman 完整解压成功作为筛选依据。在 `EighthStage` 内部，配置簇的导入表位于 `+0x18`、`fileCS` 位于 `+0x30`、节描述符位于 `+0x40`、清零区间位于 `+0x48`（存在标记的构建以 `0x00007679` 为锚点，无标记构建则根据紧随 `info[3]` 之后的 `fileCS` 指针形态定位）。字节码存根 2 通过试探解压首个压缩节数据块验证，最终输出将 RVA 缓冲区重新按 `0x200` 文件对齐紧凑排布。
{% endtab %}

{% tab title="专用 64 位 DLL" %}
早期专用 64 位 DLL（仅限 `0x20B`）无需扫描锚点，直接将配置块放置在固定偏移 `anchor = info[6] + 5592`（`0x15D8`）处：

| 相对 `anchor` 偏移 | 内容 |
| --- | --- |
| `+4` / `+8` | 导入表目录大小 / RVA |
| `+20` | 主阶段描述符密钥 |
| `+40` / `+44` | 资源目录 RVA / 大小 |
| `+48` / `+56` | `checksum2` / `checksum1` 描述符 |
| `+120` | 主阶段描述符（移位量 `21`） |
| `+184` | `xor_acc` 校验和描述符列表 |

从主表（`addr1`）出发，二级表位于 `+3632`（移位量 `19`，密钥在 `+3444`），重定位/拷贝块位于 `+9248`，四项 `key_offsets` 位于 `+9160`，代码块 1..4 分别位于 `+3712 / +3728 / +3760 / +3840`，字节码存根 1 位于 `addr4 + 3200`，`metadata` 位于 `addr5 + 12312`，字节码存根 2 位于 `metadata + 88`（即 `addr5 + 12400`），节描述符表位于 `addr5 + 11976`。

* **节描述符：** 结构为 `{dest, size, src, decompressed_size}`，文件基址按 `section_image_base = 4095 - u32@0x1080` 计算，当 `size != decompressed_size` 时执行解压。
* **656 字节头部元数据（`info[3] + 16`）：** 经 `byte_rotate2` 解密；`EntryPoint` 位于 `+0x10`，128 字节数据目录数组位于 `+0x20`（分别写回 `pe + 40` 与 `pe + 136`）。
* **托管 DLL 预填充：** 在节数据块覆盖写入 IL 方法体之前，该分支的托管构建需先从输入的加壳文件把包含 CLR 数据的节预填充到输出缓冲区，并在节还原后再把 `COR20` 头部覆写回去。
{% endtab %}

{% tab title="无标记 64 位布局" %}
新版 64 位 EXE 与 DLL 壳在 Stage 5 中移除了 `"pm\0\0cm\0\0"` 与 `0x40000000, 1` 两处特征标记：

1. **1 字节步长 LFSR 扫描：** 遍历整个 Stage 5 收集所有合法的 96 字节字节码存根，每次命中后仅前进 `+1` 字节，防止紧邻真实存根前方的巧合合法序列导致扫描跨过真实存根。
2. **`fileCS` 相对距离排序：** 检查各候选存根 `block - 0x58`（`fileCS`）处的指针，优先选取落在 `info[3]` 之后且与 `info[3]` 正向 RVA 差值最小的候选。
3. **描述符表无损探测：** 使用不修改缓冲区的 `trial_byte_rotate2` 探测候选存根附近的指针槽位，直至目标位置可解析为合法的 `{src, src_len, dst, plain_len}` 节描述符链。
4. **压缩块解压验证：** 选定存根与描述符表组合前，先对首个压缩节数据块完整执行一遍“拷贝 -> AES -> 存根置换 -> `decompress`”校验结果是否正确。

无标记构建不含 `walk3`，在完成 `.text` 页面混淆还原之后直接顺着 `DD[1]`（`IMAGE_IMPORT_DESCRIPTOR` 数组）解密导入名而不再使用 `walk5`，临时入口点/数据目录块改用元数据布局 B，保留 ASLR 标志与 `DD[5]` 基址重定位表，并且必须在 `.text` 的 `dd8` 处理完成后再回填 CLR 元数据，以免破坏位于 `.text` 内的明文 CLR 表。
{% endtab %}
{% endtabs %}
