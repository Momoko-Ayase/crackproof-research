---
description: "How the 32-bit, older DLL, and newer marker-less loader layouts differ."
---

# PE32, DLL, and marker-less layouts

## The 32-bit (PE32) flow

The 32-bit family shares the header/payload phases, then diverges completely: different anchors, an extra stage generation, and brute-forced parameters where the 64-bit flow uses fixed ones.

**The `tbl` anchor.** Located by scanning the shell region near `info[6]` for a dword equal to `info[6]` followed by a plausible shell size; the anchor is `0x88` bytes earlier. Import/resource directories are restored from `tbl + 0xBC/0xC8/0xCC`, and the **header checksum** — an XOR of `calculate_checksum` over the descriptor chain at `tbl + 0x58` — becomes a key component of every later stage. Note the consequence: stage keys depend on the *original pre-pack PE header's* checksum.

**SecondStage.** The `(offset, size)` pair at `tbl + 0x98` is unwrapped with `ss_key = header_checksum ^ first_stage_cs ^ second_stage_key` (shift 21). The constant `ss_shift = ss_size − 0xBC0` then parameterizes *every* subsequent offset — a deliberate per-build permutation of the whole stage layout. Native DLLs carry a packer-added BaseReloc data directory that the original header lacked, so the header checksum only matches with that entry zeroed; both variants are tried and the one whose ThirdStage pointer validates wins.

**ThirdStage.** The rotate shift is not recorded; it is brute-forced over `[19, 21, 17, 23, 15, 25, 13, 11]`, accepting the shift whose output contains the info-table signature (a `1`/`0x11` entry followed by a `2` entry with a plausible address). The four key offsets live `0x58` bytes before the info table, decrypted as in the 64-bit flow.

**Fourth/Fifth/Seventh.** Unwrapped from quads at `dp_base + 0x40/0x50/0x70` with keys of the form `header_checksum ^ crc32(previous region) ^ advance_key(seed)`, where each seed comes from the stage decrypted just before. The Seventh stage contains the first **bytecode stub** (located by backward-then-forward LFSR scan).

**EighthStage and its key search.** The Eighth stage key is not stored either: candidates are collected from gap heuristics around the stub (end-of-region gaps `0xD0…0x100`, stub-relative gaps, and a linear scan for non-printable dwords), each run through `advance_key(raw, 3)`, and each tried against the full stage-decrypt composite. The winner is the candidate whose result **decompresses cleanly and points inside the image** — a concrete success condition supplied by the Huffman decoder.

**The configuration cluster.** The Eighth stage holds the final table cluster at fixed offsets from a base: import table `+0x18`, file checksum chain `+0x30`, section descriptors `+0x40`, zero-fill list `+0x48`, and the file-data **bytecode stub** at `+0x4B4`. Classic builds stamp the base with the dword `0x00007679` (a build-version value that recurs in driver names — see [Htsysm kernel components](../../runtime/kernel-components.md)); builds without the stamp are located by the checksum-chain slot's shape (a pointer immediately past `info[3]` with a small 16-aligned size).

**The file decryptor, proven.** The file-data bytecode stub is not trusted to the nearest scan hit: each candidate is validated by replaying the first *compressed* block's full transform (copy → AES → translate → decompress) on a snapshot and requiring decompression to succeed. Coincidental LFSR-shaped blocks that decode to a wrong translate exist in real builds — one sits a few dozen bytes before the real stub in an observed 32-bit family — so trial-and-validate is the only safe selection.

**Output.** The 32-bit flow ends with section-table fixups, the code-page scramble (formula chosen by the `0xCC` statistic), import rebuilding (with the `.kmiat` relocation for EXEs), TLS reconstruction, and a compaction pass that repacks the RVA-laid image into a file-aligned PE. Details in [PE reconstruction](../pe-reconstruction/README.md).

## The dedicated DLL layout (older DLLs)

The older protected-DLL layout runs the same primitives but pins the configuration block to a **fixed anchor** at `keys[6] + 5592` — no scan. Every field is a fixed offset from it:

| Anchor offset | Contents |
| --- | --- |
| `+4` / `+8` | Import directory size / RVA |
| `+20` | Main descriptor encryption key |
| `+40` / `+44` | Resource directory RVA / size |
| `+48` / `+56` | Checksum descriptors (checksum2 / checksum1) |
| `+120` | Main descriptor → primary stage table |
| `+184` | XOR-accumulator checksum chain |

The stage chain then runs: primary table (shift 21) → secondary table at `+3632` (shift 19, keyed by the dword at `+3444`) → two relocation blocks at `+9248` (kind `1`/`0x11`: in-place rotate-by-3 cipher over a descriptor; kind `2`: a `(src, size, dst, verify)` copy walk whose 16-byte entries are decrypted with the rotate-by-2 cipher) → four decompression parameters at `+9160` → code blocks 1–4 at `+3712/+3728/+3760/+3840`, each with checksum-chained keys (four- and three-round triangular accumulations included) → two bytecode stubs (at `addr4 + 3200` and `metadata + 88`) → the section descriptor walk at `addr5 + 11976`.

Two details are unique to this family:

- Section descriptors store `(dest, size, src, expected_crc)`; the on-disk base is `section_image_base = 4095 − u32@0x1080`, and blocks decompress only when `size != expected_crc`. (The field is reused as the decompressed size, not a CRC.)
- The PE header metadata is delivered as a 656-byte blob at `keys[3] + 16`, decrypted with the position-keyed rotate-by-2 cipher (the same construction as [byte_rotate2](../../data-transforms/rolling-and-rotation.md#triple-byte-rotation-ciphers)): the entry point sits `0x10` into the blob and the full 128-byte data-directory array `0x20` into it; both are copied into the PE header (`pe + 40` and `pe + 136`).

Managed DLLs in this family additionally pre-fill the section containing the CLR header from the original file before section recovery, and recopy the COR20 region afterwards — the CLR structures are preserved, not encrypted.

## The marker-less layout (newer 64-bit builds)

Newer builds drop both stage-5 markers, so the walk3/walk4/walk5 slots cannot be derived from them. The layout is instead discovered structurally:

1. **Collect every LFSR-wrapped bytecode block** in the final stage (trial-decode and parse each candidate, advancing by one byte after each hit — a false positive can sit immediately before the real stub, and fixed-stride skipping would jump over it).
2. **Pick the file decryptor** as the block whose checksum-chain pointer (`block − 0x58`) lands the smallest positive distance past `info[3]`.
3. **Find the section-descriptor table** by scanning pointer slots near the stub and trial-decrypting their targets with `trial_byte_rotate2` until one parses as a plausible `(src, src_len, dst, dest_len)` descriptor.
4. **Prove the choice**: replay the first compressed block's full transform under the selected stub and require decompression to succeed.

Other differences from the marker layout: the validation-only walk3 chain is absent; imports are rebuilt from the PE import directory rather than the walk5 pointer table; the entry-point/data-directory block uses "Layout B" placement; and the code-page scramble runs *after* the managed-metadata restore (see [PE reconstruction](../pe-reconstruction/README.md)). These builds also keep their relocation tables and ASLR flags — they are not `/FIXED`.

