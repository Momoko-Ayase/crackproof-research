---
description: "受保護 Android ELF64 程式庫與 IL2CPP 中繼資料的逐步驗證檢核表。"
icon: list-check
---

# 驗證檢核表

每個待處理的 Android `.so` 與 `global-metadata.dat` 都必須依序通過下列結構檢查；只要違反任一結構不變條件，還原流程就會立即中止，不會輸出不完整的檔案。

{% stepper %}
{% step %}
## ELF 辨識與 `SHT_LOUSER` 邊界

* 驗證檔案為 ELF64、little-endian、`EM_AARCH64`（`183`）、`e_phentsize == 0x38`、`e_shentsize == 0x40`，且具備合法 UTF-8 編碼的 `.shstrtab`。
* 要求具備 `.dynsym`、`.dynstr`、`.gnu.version`、`.gnu.version_r`，以及至少一個符號雜湊區段（`.gnu.hash` 或 `.hash`）。執行還原時另要求 `.dynamic`、`.rela.dyn` 與 `.rela.plt` 各自恰好出現一次。
* 要求最後一筆區段標頭為唯一的 `SHT_LOUSER`（`0x80000000`）私有區段，且起始位置對齊檔案內 `PT_LOAD` 範圍結尾的 16 位元組邊界（中間若有空隙須全數補零）。
{% endstep %}

{% step %}
## Stage 1 與 Stage 2 串流擷取

* 解碼位於 `section_offset + outer_size` 的 32 位元組 Stage 1 字組標頭，並要求滿足 `reserved == 0`、`size_copy == payload_size`、`payload_size > 0 && payload_size % 4 == 0`、`payload_offset >= 0x20`、`payload_offset + payload_size <= section_size - outer_size`、`entry_offset < payload_size` 以及 `protect_size <= payload_size`。
* 解析 Stage 2 的 `0x5C` 記錄描述元表，範圍不超過最小的非零 payload 位移（筆數為 `dw0`，上限 256 筆），並對每個切片檢查 `id_copy == command_id` 以及父串流邊界。
* 要求每個 Huffman/LZ 壓縮區塊的位元消耗量完全吻合（`div_ceil(consumed_bits, 8) == src_len`）、輸出長度完全吻合（`output_pos == out_len`），且結束時 `pending == 0`。
* 要求具備基本還原模組 `0x9B`、`0x9D` 與 `0x9E`（若存在選用的 `0x96`、`0x98` 與 `0x0C` 則一併採用）。相同模組 ID 若出現重複記錄，SHA-256 雜湊值相同者剔除重複項，不一致者直接拒絕。
{% endstep %}

{% step %}
## 動態表重建與 ELF 輸出

* 驗證 `0x9E` 隱藏符號索引（`0 < target_index < symbol_count` 且不重複）與 `.dynstr` 邊界；移除保護器附加於尾端的符號（`dlerror`、`__stack_chk_guard`、`__stack_chk_fail`），在 `0x96` 存在時還原被打亂的輔助符號索引，辨識被省略的 `libc` PLT 空缺，將已定義符號的重定位正規化並排序為開頭連續的 `R_AARCH64_RELATIVE` 前綴（更新 `DT_RELACOUNT`），並在 `0x98` 存在時執行建構函式復原。
* 將重建後的各動態表放入 `.dynsym` 之後的可用區間或附加於尾端的 `PF_R` `PT_LOAD` 程式區段，移除 `SHT_LOUSER`，將 `e_entry` 清為 `0`，把非 `SHF_ALLOC` 區段移至可載入區段之後，以原子方式寫入檔案，再從磁碟重新解析驗證。
* 執行寫入後的必要檢查（ELF 可正常解析、`PT_LOAD` 檔案邊界合法、`.shstrtab` 完整、不含 `SHT_LOUSER`、`e_entry == 0`，且 `.dynsym` / `.rela.dyn` / `.rela.plt` 筆數完全吻合），並記錄跨表連結器診斷資訊。
{% endstep %}

{% step %}
## IL2CPP 中繼資料驗證

* 要求魔術數值為 `0xFAB11BAF`，且資料表配置通過對應版本的結構驗證：支援版本 `24`（`v24.1` 須搭配同一應用程式的模組 `0x0C`）、`29`、`31`（帶種子的五回合逆運算，並以依表格順序的 `-GMD` 重映射作為備援）或 `39`（精簡型 12 位元組區段目錄）。
* 已符合標準順序的中繼資料維持原樣不改動（具冪等性），並在還原後驗證各映像的方法歸屬區間連續無間斷，且欄位值皆符合標準的 `0x06000000 | rid` 或 `0..active_count` 範圍。
{% endstep %}
{% endstepper %}
