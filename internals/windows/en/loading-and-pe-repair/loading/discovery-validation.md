---
description: "Candidate offset validation, trial decompression checks, and .text page-scramble selection."
icon: magnifying-glass
---

# Structural discovery and validation

Because stage sizes shift per build (`ss_shift` on PE32, `anchor_extra` on 64-bit) and modern 64-bit builds omit fixed Stage 5 markers, static recovery validates every candidate offset, shift, and seed before mutating the working image:

* **Anchor and table invariants:** require `u32@anchor == info[3]`, `(1, 0, info[3], 0)` at Stage 2 `table_start`, and in-image `{offset, size}` bounds before unwrapping any stage descriptor.
* **Strict bytecode VM grammar:** parse candidate 96-byte LFSR slots all the way to `0xC3` (`RET`), rejecting any non-`AL` `ModR/M` encoding (`mod != 3`, `rm != 0`, or `reg > 1`) and advancing scans by 1 byte where false positives can precede the real stub.
* **Non-destructive descriptor lookahead:** inspect candidate pointer targets with `trial_byte_rotate2` and verify that both `src + section_data_file_base` and `dst + plain_len` fit inside the file and `SizeOfImage`.
* **First-compressed-block proof:** never accept a bytecode stub or `EighthStage` seed from raw-copy blocks alone; replay AES + bytecode translation + `decompress` on the first compressed block and require `written == plain_len` with valid Huffman tree walks.
* **Three-tier `.text` page-scramble (`dd8`) selection:**
  1. On 64-bit images, check the 18-byte CRT entry stub (`48 83 EC ib / E8 rel32 / 48 83 C4 ib / E9 rel32`) across `unchanged`, `shift 0`, and `shift 15`, picking the unique mode whose `call` and `jmp` targets both stay inside `.text`.
  2. Otherwise on 64-bit images, score interior `.text` pages by total run length of `0xC3` (`RET`) followed by `>= 4` `0xCC` padding bytes, requiring a positive delta `>= 8` over the unchanged baseline.
  3. Only when all `RET + int3` scores are `0` on 64-bit (and always on 32-bit across `page + 1` vs `0x8000 * (page + 1)`), fall back to counting mutated positions that become `0xCC`, requiring both `>= 2x` baseline and `>= 8` hits before modifying `.text`.

If all candidates fail validation at any stage, recovery terminates with an explicit error rather than emitting a partially decoded PE.
