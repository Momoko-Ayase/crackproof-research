---
description: "整理乾淨的 ELF64 區段標頭表、將 e_entry 歸零、原子寫入並驗證輸出檔。"
icon: file-export
---

# ELF 輸出

`PT_LOAD` 載入段與動態連結表重建完成後，ELF 收尾步驟會移除僅供保護機制使用的結構，並重寫檔案尾端的非載入區段：

1. **移除 `SHT_LOUSER`：** 捨棄尾端的私有區段標頭，且不將任何 Stage 1／Stage 2 payload 位元組複製到輸出檔案中。
2. **將 `e_entry` 歸零：** Android 共用程式庫是透過 `.init_array` 而非 `e_entry` 執行原生建構函式，因此會將 `e_entry` 設為 `0`。
3. **搬移非 `SHF_ALLOC` 區段：** 將保留下來的非載入區段（例如 `.shstrtab`）緊密排列在所有可載入段（包含新附加的 `PF_R` `PT_LOAD` 段）之後，驗證 `.shstrtab` 內容，最後在檔尾寫入更新後的區段標頭表（`Elf64_Shdr`）並更新 `e_shoff` 與 `e_shnum`。
4. **原子寫入與重新剖析：** 寫入磁碟時會先寫至暫存檔，再透過原子重新命名完成輸出，隨後直接讀取寫出的位元組重新剖析驗證。

{% hint style="info" %}
**寫入後的強制檢查與結構診斷。** 輸出驗證分為兩個層級：
* **硬性檢查失敗（中止復原）：** 小端序 AArch64 ELF64 剖析失敗、`PT_LOAD` 檔案範圍超出輸出檔案總長度、`.shstrtab` 格式損毀、仍殘留 `SHT_LOUSER` 私有區段、`e_entry` 非零，或 `.dynsym`／`.rela.dyn`／`.rela.plt` 的項目數量與重建後的表格不一致。
* **跨表結構診斷（以警告回報）：** 模擬動態連結器檢查 `PT_LOAD` 的對齊、同餘與重疊狀況、`DT_*` 標籤與區段標頭的一致性、`DT_RELACOUNT` 前綴排序、符號雜湊桶（bucket）邊界、重定位目標位址與符號索引範圍，以及 `.init_array`／`.fini_array` 函式指標的有效性。
{% endhint %}
