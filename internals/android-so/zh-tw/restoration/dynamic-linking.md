---
description: "重建動態符號表、雜湊表、重定位表、PLT 空缺、建構函式與 PT_LOAD 配置。"
icon: link
---

# 動態連結

將 `0x9D` 主容器內的位元組填回先前被挖空的 `PT_LOAD` 範圍後，靜態復原接著會重建遭 CrackProof 移除或拆散至 `0x9D`、`0x9E`、`0x96` 與 `0x98` 的各個動態連結表。

{% stepper %}
{% step %}
## 復原隱藏符號並移除保護器尾端匯入項

模組 `0x9E` 開頭為 `{u32 blob_size, u32 secondary_record_count}`，`+0x08` 處緊接著 `{u32 count, u32 symbol_offset, u32 index_offset, u32 string_offset}`，後續依序為 `count` 筆 24 位元組的 `Elf64_Sym` 項目、`count` 個 `u32` 目標 `.dynsym` 索引，以及以 NUL 結尾的符號名稱（尾端含 0 至 3 位元組的零值填補）。每筆修補紀錄都必須指向不重複的索引 `0 < target_index < symbol_count`，且 `st_name` 對應的名稱必須能放入 `.dynstr` 範圍內（寫入已清零的空間，或與既有字串完全一致）。

若 `0x9E` 最大 `target_index` 之後的尾端符號全數屬於保護器注入的匯入項（限於 `{"dlerror", "__stack_chk_guard", "__stack_chk_fail"}`），復原流程會在附加輔助符號之前，先移除這些尾端符號以及所有參照它們的重定位紀錄。
{% endstep %}

{% step %}
## 附加輔助符號並還原重定位索引置換

`0x9D` 內的輔助容器提供 `relocation1`（`.rela.dyn` 候選項）、`relocation2`（`.rela.plt` 候選項）、輔助動態符號表 `.dynsym`（索引 `0` 為空項目，另含 `N - 1` 個外部符號），以及輔助字串表 `.dynstr`。其中非空的符號會附加至主 `.dynsym` 尾端（同時相應擴充 `.dynstr`，並在 `.gnu.version` 中指派 `VER_NDX_GLOBAL = 1`，而 `.gnu.version_r` 則沿用已復原的主映像內容）。

當模組 `0x96` 存在（且 `N > 1`）時，`relocation1` 與 `relocation2` 內的非零輔助符號索引（`1..N-1`）會依重定位列號 `row`，以取自 `0x96` 的 32 位元 `auxiliary_symbol_seed` 逐列旋轉：

```text
s2       = (seed * seed) & 0xFFFFFFFF
left     = ((s2 >> (row & 0x1B)) + 0x1BC5) & 0xFFFFFFFF
right    = (((s2 << (row & 3)) & 0xFFFFFFFF) + 0x2048) & 0xFFFFFFFF
rotation = (left | right) % (N - 1)
```

先對 `N - 1` 取模以反向還原逐列旋轉，再加上 `old_symbol_count - 1`，讓每個 `r_info` 正確指向合併後的 `.dynsym` 槽位。
{% endstep %}

{% step %}
## 辨識五個被省略的 `libc` PLT 空缺

CrackProof 會在 `relocation2` 中省略最多五個標準 `libc` 字串與記憶體函式（`strlen`、`strcmp`、`memset`、`strcpy`、`strchr`），在 `.got.plt`（略過開頭 `0x18` 位元組標頭後）留下未被參照的槽位。復原流程會將每個空缺槽位對應至 `.plt + 0x20 + slot * 0x10`（包含編譯器產生的 `ADRP X16/X17; ADD; BR` 跳板指令），掃描 `.text` 內各個 AArch64 呼叫點的引數暫存器與回傳值用法以判定對應函式，隨後補上 `SHN_UNDEF` `STT_FUNC` 符號，並將缺少的 `R_AARCH64_JUMP_SLOT`（`0x402`）紀錄寫入 `.rela.plt`。
{% endstep %}

{% step %}
## 正規化 `.rela.dyn`、重建符號雜湊表與復原建構函式

在 `.rela.dyn` 中，任何目標符號已定義（`st_shndx != SHN_UNDEF`）的重定位紀錄（`R_AARCH64_ABS64 = 0x101` 或 `R_AARCH64_GLOB_DAT = 0x401`），都會轉換為 `R_AARCH64_RELATIVE`（`0x403`），並將 `r_addend` 更新為 `st_value + r_addend`。所有 `R_AARCH64_RELATIVE` 項目會依 `r_offset` 排序並集中至 `.rela.dyn` 開頭，同時將 `DT_RELACOUNT` 更新為此連續前綴的項目數量。

接著依輸入 ELF 原先帶有的符號雜湊區段（`.gnu.hash`、SysV `.hash` 或兩者皆有），以最終版 `.dynsym` 重新計算雜湊表。若模組 `0x98` 存在，帶執行上限的 AArch64 直譯器會從 `entry_offset` 開始模擬執行（初始狀態為 `X0 = runtime`、`[X0 + 8] = image_base`，並預期執行至 `RET` 時 `W0 == 1`），藉此復原被隱藏的建構函式指標、替換 `.init_array` 中的 Stage 1 啟動槽位、剔除僅含 `RET`（`0xD65F03C0`）的佔位項，並同步更新 `.init_array`／`.fini_array` 的區段大小與 `DT_INIT_ARRAYSZ`／`DT_FINI_ARRAYSZ`。
{% endstep %}

{% step %}
## 原地寫回重建表或附加唯讀 `PF_R` `PT_LOAD` 段

若重建後的 `.dynsym`、`.gnu.version`、符號雜湊表、`.dynstr`、`.rela.dyn` 與 `.rela.plt` 總長度不超過原本從 `.dynsym` 起始的檔案區間，便會直接原地寫回。若擴充後的表格超出原區間，復原流程會在檔尾附加一個新的唯讀（`PF_R`）`PT_LOAD` 段，對齊至既有 `PT_LOAD` 段的最大 `p_align`，並一併更新 `DT_SYMTAB`、`DT_STRTAB`、`DT_STRSZ`、`DT_GNU_HASH`／`DT_HASH`、`DT_VERSYM`、`DT_RELA`、`DT_RELASZ`、`DT_JMPREL` 與 `DT_PLTRELSZ`。

為了在不覆寫已映射位元組的前提下插入新增的 `Elf64_Phdr`，重建流程會優先利用程式標頭表尾端的閒置空間；若無空間，且 `PT_LOAD` 內有兩個以上的 `PT_NOTE` 標頭，則重用其中多餘的 `PT_NOTE` 項目；否則便將整個程式標頭表搬移至新附加 `PT_LOAD` 段的開頭，並更新 `e_phoff` 與 `PT_PHDR`。
{% endstep %}
{% endstepper %}
