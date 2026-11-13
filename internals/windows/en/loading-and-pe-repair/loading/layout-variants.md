---
description: "Structural differences across standard/compact PE32 shells, dedicated 64-bit DLLs, and marker-less 64-bit builds."
icon: code-branch
---

# PE32, DLL, and marker-less layouts

{% tabs %}
{% tab title="PE32 (Standard & Compact)" %}
32-bit (`0x10B`) containers run an eight-stage chain (`SecondStage` through `EighthStage`) parameterized by a per-build stage-size delta `ss_shift`. Two `tbl` layouts appear in observed builds (and older compact shells may encrypt the full `info[5]` payload in `payload_xor_chain`):

| Structure / offset | Standard PE32 (`match - 0x88`) | Compact PE32 (`match - 0x78`) |
| --- | --- | --- |
| `info[6]` match inside `tbl` | `tbl + 0x88` | `tbl + 0x78` |
| Header-checksum descriptor chain | `tbl + 0x58` | `tbl + 0x50` |
| `SecondStage` `(offset, size)` | `tbl + 0x98` | `tbl + 0x88` |
| `first_stage_cs` / `second_stage_cs` | `tbl + 0xA8` / `tbl + 0xB0` | `tbl + 0x98` / `tbl + 0xA0` |
| Saved Import RVA | `tbl + 0xBC` | `tbl + 0xAC` |
| Saved Resource `(RVA, size)` | `tbl + 0xC8` / `tbl + 0xCC` | `tbl + 0xB0` / `tbl + 0xB4` |
| Per-build stage bias `ss_shift` | `ss_size - 0xBC0` | `ss_size - 0xAEC` |
| `SevenStage` seed (`seven_key`) | `~u32@(cs1_addr + cs1_size - 0x10)` | `~u32@(cs1_addr + cs1_size - 0x0C)` |

Compact PE32 also shifts its `SecondStage`-internal pointers to `third_pair_off = 0xAB4 + ss_shift` and `forth_key_off / third_key_off / cs_base_off / dp_base_off = 0x94C / 0x950 / 0x954 / 0x9C4 + ss_shift`.

* **Header checksum & DLL `BaseReloc` trial:** `header_checksum` XORs `calculate_checksum` across the pre-pack PE header regions. Native PE32 DLLs carry a packer-populated `DD[5]` (`BaseReloc`) entry that was zero in the pre-pack header, so recovery tests both the as-is header and a copy with `DD[5]` zeroed, keeping whichever validates `ThirdStage`.
* **`ThirdStage` shift brute-force:** tries `[19, 21, 17, 23, 15, 25, 13, 11]` until the info-table signature (`1`/`0x11` followed by `2` with an in-image address) appears; the four `key_offsets` sit `0x58` bytes earlier.
* **Dynamic `advance_key` round counts (`Fourth` / `Fifth` / `Seventh` / `Eighth`):** instead of fixed round counts, PE32 counts leading active 16-byte helper descriptors (`size > 4`, stopping at the first empty slot) in the four-slot tables at `dp_base` and `dp_base + 0x80`.
* **`EighthStage` key & cluster discovery:** gap heuristics and non-printable dword scans supply `EighthStage` seed candidates, validated by clean Huffman decompression. Inside `EighthStage`, the configuration cluster places imports at `+0x18`, `fileCS` at `+0x30`, section descriptors at `+0x40`, and zero-fill ranges at `+0x48` (anchored on stamp `0x00007679` when present, or on `fileCS` pointer shape immediately past `info[3]` on stampless builds). Bytecode stub 2 is verified by trial-decompressing the first compressed section block, and final output compacts the RVA buffer back to `0x200` file alignment.
{% endtab %}

{% tab title="Dedicated 64-bit DLL" %}
Older dedicated 64-bit DLLs (`0x20B` only) omit anchor scanning and place the configuration block at fixed offset `anchor = info[6] + 5592` (`0x15D8`):

| Offset from `anchor` | Contents |
| --- | --- |
| `+4` / `+8` | Import directory size / RVA |
| `+20` | Primary stage descriptor key |
| `+40` / `+44` | Resource directory RVA / size |
| `+48` / `+56` | `checksum2` / `checksum1` descriptors |
| `+120` | Primary stage descriptor (shift `21`) |
| `+184` | `xor_acc` checksum descriptor list |

From the primary table (`addr1`), the secondary table sits at `+3632` (shift `19`, key at `+3444`), relocation/copy blocks at `+9248`, the four `key_offsets` at `+9160`, code blocks 1..4 at `+3712 / +3728 / +3760 / +3840`, bytecode stub 1 at `addr4 + 3200`, `metadata` at `addr5 + 12312`, bytecode stub 2 at `metadata + 88` (`addr5 + 12400`), and the section-descriptor walk at `addr5 + 11976`.

* **Section descriptors:** `{dest, size, src, decompressed_size}` with `section_image_base = 4095 - u32@0x1080`, decompressing when `size != decompressed_size`.
* **656-byte header metadata (`info[3] + 16`):** decrypted with `byte_rotate2`; `EntryPoint` is at `+0x10` and the 128-byte data-directory array is at `+0x20` (copied to `pe + 40` and `pe + 136`).
* **Managed DLL pre-fill:** before section blocks overwrite IL method bodies, managed builds in this family pre-fill the CLR-bearing section from the protected file and re-overlay the `COR20` header afterward.
{% endtab %}

{% tab title="Marker-less 64-bit" %}
Modern 64-bit EXE and DLL shells omit both `"pm\0\0cm\0\0"` and `0x40000000, 1` in Stage 5:

1. **1-byte-stepped LFSR scan:** collect every valid 96-byte bytecode stub across Stage 5, stepping by `+1` byte after each hit so a coincidental valid parse immediately preceding the real stub never causes the scan to step over it.
2. **`fileCS` proximity ranking:** evaluate candidate stubs by checking `block - 0x58` (`fileCS`) for the smallest positive RVA distance past `info[3]`.
3. **Descriptor-table probe:** scan pointer slots near the candidate stub with non-mutating `trial_byte_rotate2` until a target parses as a valid `{src, src_len, dst, plain_len}` section chain.
4. **Compressed-block proof:** replay copy -> AES -> stub translate -> `decompress` on the first compressed section block before accepting the stub/table pair.

Marker-less builds omit `walk3`, decrypt imports from `DD[1]` (`IMAGE_IMPORT_DESCRIPTOR`s) instead of `walk5` after `.text` page-scramble recovery, use Metadata Layout B for the transient EP/directory block, preserve ASLR flags and `DD[5]` relocations, and restore CLR metadata after `.text` `dd8` so plaintext CLR tables inside `.text` are not corrupted.
{% endtab %}
{% endtabs %}
