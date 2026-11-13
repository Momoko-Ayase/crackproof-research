---
description: "Step-by-step fail-closed validation checks for protected Android ELF64 libraries and IL2CPP metadata."
icon: list-check
---

# Validation checklist

Every candidate Android `.so` and `global-metadata.dat` must pass the structural checks below in order; any failed hard invariant aborts recovery without emitting a partial output file.

{% stepper %}
{% step %}
## ELF recognition and `SHT_LOUSER` bounds

* Verify ELF64, little-endian, `EM_AARCH64` (`183`), `e_phentsize == 0x38`, `e_shentsize == 0x40`, and a valid UTF-8 `.shstrtab`.
* Require `.dynsym`, `.dynstr`, `.gnu.version`, `.gnu.version_r`, and at least one symbol-hash section (`.gnu.hash` and/or `.hash`). Restoration also requires `.dynamic`, `.rela.dyn`, and `.rela.plt` once each.
* Require exactly one `SHT_LOUSER` (`0x80000000`) section as the final section header, starting at the 16-byte-aligned end of the file-backed `PT_LOAD` range (with zero padding in any gap).
{% endstep %}

{% step %}
## Stage 1 and Stage 2 stream extraction

* Decode the 32-byte Stage 1 word header at `section_offset + outer_size` and require `reserved == 0`, `size_copy == payload_size`, `payload_size > 0 && payload_size % 4 == 0`, `payload_offset >= 0x20`, `payload_offset + payload_size <= section_size - outer_size`, `entry_offset < payload_size`, and `protect_size <= payload_size`.
* Parse Stage 2 `0x5C` record tables up to the earliest non-zero payload offset (`dw0` count, capped at 256), checking `id_copy == command_id` and parent stream bounds on every slice.
* Require exact compressed bit consumption (`div_ceil(consumed_bits, 8) == src_len`), exact output size (`output_pos == out_len`), and `pending == 0` on every Huffman/LZ block.
* Require baseline modules `0x9B`, `0x9D`, and `0x9E` (using optional `0x96`, `0x98`, and `0x0C` when present). Deduplicate identical module SHA-256 digests and reject conflicting digests for the same module ID.
{% endstep %}

{% step %}
## Dynamic-table reconstruction and ELF output

* Verify `0x9E` hidden-symbol indices (`0 < target_index < symbol_count`, unique) and `.dynstr` bounds; strip protector tail symbols (`dlerror`, `__stack_chk_guard`, `__stack_chk_fail`), unpermute auxiliary symbol indices via `0x96` when present, classify any omitted `libc` PLT holes, normalize defined-symbol relocations into a sorted `R_AARCH64_RELATIVE` prefix (`DT_RELACOUNT`), and apply `0x98` constructor recovery when present.
* Place rebuilt tables in the post-`.dynsym` window or an appended `PF_R` `PT_LOAD`, remove `SHT_LOUSER`, clear `e_entry` to `0`, relocate non-`SHF_ALLOC` sections after loadable segments, write atomically, and re-parse from disk.
* Enforce hard post-write checks (parse validity, `PT_LOAD` file bounds, `.shstrtab`, no `SHT_LOUSER`, `e_entry == 0`, exact `.dynsym` / `.rela.dyn` / `.rela.plt` counts) and record cross-table linker diagnostics.
{% endstep %}

{% step %}
## IL2CPP metadata verification

* Require `0xFAB11BAF` and a validated table layout for version `24` (`v24.1` paired with module `0x0C` from the same application), `29`, `31` (seeded five-round inverse with structural `-GMD` fallback), or `39` (compact 12-byte section directory).
* Leave already-canonical metadata untouched (idempotence) and verify contiguous single-image method ownership and canonical `0x06000000 | rid` / `0..active_count` bounds after restoration.
{% endstep %}
{% endstepper %}
