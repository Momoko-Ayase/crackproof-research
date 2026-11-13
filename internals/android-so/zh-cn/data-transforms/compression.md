---
description: "解码 3 字节结点 Huffman 表、16 位前缀表与四种 LZ/游程符号模式。"
icon: file-zipper
---

# Huffman 与 LZ 压缩

压缩容器块与 [Windows Huffman/LZ 格式](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/data-transforms/compression)共用同一套 3 字节 Huffman 树表项和四模式符号编码。表中每个结点占 3 字节（`u16 value`、`u8 bit_len`）。前 8 位输入用于查找初始根结点，16 位前缀查找表负责加速短码；更长的编码则按输入位在左右子结点（`value` 与 `value + 1`）中逐层向下索引，直至命中叶子结点（`value & 0x8000 != 0`）。

## 符号模式

清除叶子结点值的第 15 位后可得到一个 10 位符号：第 `8..9` 位选择模式，第 `0..7` 位携带 `payload`。16 位累加器 `pending` 初始为 `0`：

| 模式（`sym & 0x300`） | 载荷（`sym & 0xFF`） | 操作 |
| --- | --- | --- |
| `0x000` | 字面量字节 | 直接输出 1 字节 `payload`（要求此时 `pending == 0`） |
| `0x100` | 计数字节 | 若 `pending > 0xFF` 则拒绝；令 `pending = (pending << 8) \| payload`，不产生输出 |
| `0x200` | 单元宽度（`1`、`2` 或 `4`） | 令 `reps = max(pending, 1)`，将刚写出的 `payload` 字节单元重复追加 `reps` 次（共写入 `reps * payload` 字节），随后将 `pending` 重置为 `0` |
| `0x300` | 匹配长度（`length`） | 从当前输出位置向后回溯 `distance = pending + length` 字节处拷贝 `length` 字节，随后将 `pending` 重置为 `0` |

<details>
<summary>符号解码示例</summary>

假设当前 `output_pos = 4`，输出缓冲区末尾刚写入 4 字节小端序字 `11 22 33 44`：

1. 叶子 `0x8103`（`mode = 0x100`，`payload = 0x03`）：`pending` 变为 `0x0003`，写出 0 字节。
2. 叶子 `0x8204`（`mode = 0x200`，`payload = 4`）：单元宽度为 `4` 字节且 `reps = 3`，因此将 `11 22 33 44` 重复 3 次（写出 `12` 字节，`output_pos = 16`），并将 `pending` 重置为 `0`。
3. 叶子 `0x8104`（`mode = 0x100`，`payload = 0x04`）后跟 `0x8306`（`mode = 0x300`，`payload = 6`）：`length = 6`，`distance = 4 + 6 = 10`，从 `output[6..12]` 拷贝 6 字节，并将 `pending` 重置为 `0`。
</details>

## 校验条件

* **游程填充**（`0x200`）：`payload` 只能取 `1`、`2` 或 `4`，输出缓冲区内已写入字节数不得少于 `payload`，且 `output_pos + max(pending, 1) * payload` 不得超出 `out_len`。
* **LZ 回溯匹配**（`0x300`）：`distance = pending + length` 必须满足 `distance <= output_pos` 且 `output_pos + length <= out_len`（当 `distance < length` 时，允许按字节顺序重叠拷贝）。
* **精确收尾**：仅当 `output_pos == out_len`、`pending == 0` 且 `div_ceil(consumed_bits, 8) == src_len` 同时成立时，解压才算成功。任何结点下标越界、零位宽叶子、`pending` 溢出或尾部残留未消耗字节，都会判定容器解码失败。
