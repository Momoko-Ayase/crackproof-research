---
description: "解碼 3 位元組 Huffman 樹森林、16 位元前綴表與四種 LZ／游程編碼模式。"
icon: file-zipper
---

# Huffman 與 LZ 壓縮

壓縮容器區塊採用與 [Windows Huffman/LZ 格式](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/data-transforms/compression)完全相同的 3 位元組 Huffman 樹節點結構與四模式 token 編碼。表中每個節點占 3 位元組（`u16 value`、`u8 bit_len`）：先由 8 位元查詢選擇起始根節點，並透過 16 位元前綴表加速短碼解碼；較長的編碼則每次讀取 1 個輸入位元，沿相鄰子節點配對（`value` 與 `value + 1`）向下走訪，直到抵達葉節點（`value & 0x8000 != 0`）。

## 四種編碼模式

清除葉節點 `value` 的第 15 位元後，會得到 10 位元符號 `sym`：位元 `8..9` 決定模式，位元 `0..7` 攜帶 `payload`。16 位元累加器 `pending` 初始值為 `0`：

| 模式（`sym & 0x300`） | 負載（`sym & 0xFF`） | 運作方式 |
| --- | --- | --- |
| `0x000` | 字面值位元組 | 直接輸出 1 位元組 `payload`（此時 `pending` 必須為 `0`） |
| `0x100` | 計數位元組 | 若 `pending > 0xFF` 則拒絕；否則設定 `pending = (pending << 8) \| payload`，不輸出任何位元組 |
| `0x200` | 單位寬度（`1`、`2` 或 `4`） | 令 `reps = max(pending, 1)`；將前一個已輸出的 `payload` 位元組單位重複寫出 `reps` 次（共 `reps * payload` 位元組），接著重設 `pending = 0` |
| `0x300` | 比對長度（`length`） | 從目前輸出位置往回 `distance = pending + length` 位元組處複製 `length` 位元組，接著重設 `pending = 0` |

<details>
<summary>編碼展開逐步示範</summary>

假設輸出緩衝區尾端已寫入 4 位元組小端序字組 `11 22 33 44`，目前 `output_pos = 4`：

1. 葉節點 `0x8103`（`mode = 0x100`、`payload = 0x03`）：`pending` 變為 `0x0003`，寫出 0 位元組。
2. 葉節點 `0x8204`（`mode = 0x200`、`payload = 4`）：單位寬度為 `4` 位元組且 `reps = 3`，因此將 `11 22 33 44` 重複寫出 3 次（共寫入 `12` 位元組，`output_pos = 16`），並將 `pending` 重設為 `0`。
3. 葉節點 `0x8104`（`mode = 0x100`、`payload = 0x04`）後接 `0x8306`（`mode = 0x300`、`payload = 6`）：`length = 6`、`distance = 4 + 6 = 10`，從 `output[6..12]` 複製 6 位元組至輸出尾端，並將 `pending` 重設為 `0`。
</details>

## 驗證條件

* **游程填充（`0x200`）：** `payload` 必須為 `1`、`2` 或 `4`，輸出緩衝區內至少已存在 `payload` 位元組，且 `output_pos + max(pending, 1) * payload` 不得超過 `out_len`。
* **LZ 反向參照（`0x300`）：** `distance = pending + length` 必須滿足 `distance <= output_pos` 且 `output_pos + length <= out_len`（當 `distance < length` 時，允許逐位元組向前重疊複製）。
* **精確完成檢查：** 唯有同時滿足 `output_pos == out_len`、`pending == 0` 與 `div_ceil(consumed_bits, 8) == src_len` 時，解壓縮才算成功。凡是節點索引越界、零位元葉節點、`pending` 溢位，或是殘留未消耗的尾端位元組，都會判定容器解碼失敗。
