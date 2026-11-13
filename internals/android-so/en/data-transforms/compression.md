---
description: "Decode 3-byte Huffman forests, 16-bit prefix tables, and the four LZ/run-fill token modes."
icon: file-zipper
---

# Huffman and LZ compression

Compressed container blocks use the same 3-byte Huffman tree entries and four-mode token encoding as the [Windows Huffman/LZ format](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/data-transforms/compression). Each node in the table is 3 bytes (`u16 value`, `u8 bit_len`). An 8-bit lookup selects the initial root node, and a 16-bit prefix table accelerates short codes; longer codes step down sibling pairs (`value` and `value + 1`) one input bit at a time until reaching a leaf (`value & 0x8000 != 0`).

## Token modes

Clearing bit 15 of a leaf value leaves a 10-bit symbol: bits `8..9` select the mode and bits `0..7` carry `payload`. A 16-bit accumulator `pending` starts at `0`:

| Mode (`sym & 0x300`) | Payload (`sym & 0xFF`) | Operation |
| --- | --- | --- |
| `0x000` | Literal byte | Emit `payload` as one byte (`pending` must be `0`) |
| `0x100` | Count byte | Reject if `pending > 0xFF`; set `pending = (pending << 8) \| payload` and emit nothing |
| `0x200` | Unit width (`1`, `2`, or `4`) | Let `reps = max(pending, 1)`; repeat the previously written `payload`-byte unit `reps` times (`reps * payload` bytes total), then reset `pending = 0` |
| `0x300` | Match length (`length`) | Copy `length` bytes from `distance = pending + length` bytes behind the current output position, then reset `pending = 0` |

<details>
<summary>Worked token trace</summary>

Suppose the output buffer already ends with the 4-byte little-endian word `11 22 33 44` at `output_pos = 4`:

1. Leaf `0x8103` (`mode = 0x100`, `payload = 0x03`): `pending` becomes `0x0003`; 0 bytes written.
2. Leaf `0x8204` (`mode = 0x200`, `payload = 4`): unit width is `4` bytes and `reps = 3`, so `11 22 33 44` is repeated 3 times (`12` bytes written, `output_pos = 16`), and `pending` resets to `0`.
3. Leaf `0x8104` (`mode = 0x100`, `payload = 0x04`) followed by `0x8306` (`mode = 0x300`, `payload = 6`): `length = 6`, `distance = 4 + 6 = 10`, copying 6 bytes from `output[6..12]` and resetting `pending = 0`.
</details>

## Validation invariants

* **Run-fill (`0x200`):** `payload` must be `1`, `2`, or `4`, at least `payload` bytes must already exist in the output buffer, and `output_pos + max(pending, 1) * payload` must not exceed `out_len`.
* **Back-reference (`0x300`):** `distance = pending + length` must satisfy `distance <= output_pos` and `output_pos + length <= out_len` (overlapping byte-by-byte forward copies are valid when `distance < length`).
* **Exact completion:** expansion succeeds only when `output_pos == out_len`, `pending == 0`, and `div_ceil(consumed_bits, 8) == src_len`. Any out-of-range node index, zero-bit leaf, overflowed `pending`, or unconsumed trailing byte fails the container decode.
