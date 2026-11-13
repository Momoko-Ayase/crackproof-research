---
description: "Rebuild .dynsym, .dynstr, symbol hashes, relocations, PLT holes, constructors, and PT_LOAD table placement."
icon: link
---

# Dynamic linking

Once the primary `0x9D` container has written the hollowed `PT_LOAD` bytes back into the working ELF image, static restoration reconstructs the dynamic-linking tables that CrackProof stripped or split across `0x9D`, `0x9E`, `0x96`, and `0x98`.

{% stepper %}
{% step %}
## Restore hidden symbols and strip protector tail imports

Module `0x9E` begins with `{u32 blob_size, u32 secondary_record_count}` followed at `+0x08` by `{u32 count, u32 symbol_offset, u32 index_offset, u32 string_offset}`, `count` 24-byte `Elf64_Sym` entries, `count` `u32` target `.dynsym` indices, and NUL-terminated symbol names (0 to 3 bytes of zero padding). Each patch must target a unique index `0 < target_index < symbol_count`, and its name at `st_name` must fit within `.dynstr` (writing into zeroed space or matching identical existing text).

If trailing symbols after `0x9E`'s highest `target_index` consist solely of protector-injected imports from `{"dlerror", "__stack_chk_guard", "__stack_chk_fail"}`, those tail symbols and any relocations referencing them are removed before appending auxiliary symbols.
{% endstep %}

{% step %}
## Append auxiliary symbols and unpermute relocation indices

The auxiliary container from `0x9D` provides `relocation1` (`.rela.dyn` candidates), `relocation2` (`.rela.plt` candidates), an auxiliary `.dynsym` (null entry at `0` plus `N - 1` external symbols), and an auxiliary `.dynstr`. Its non-null symbols are appended to `.dynsym` (with `.dynstr` extended accordingly and `VER_NDX_GLOBAL = 1` assigned in `.gnu.version`, while `.gnu.version_r` comes from the restored primary image).

When module `0x96` is present (`N > 1`), non-zero auxiliary symbol indices (`1..N-1`) in `relocation1` and `relocation2` are rotated per relocation row `row` using the 32-bit `auxiliary_symbol_seed` extracted from `0x96`:

```text
s2       = (seed * seed) & 0xFFFFFFFF
left     = ((s2 >> (row & 0x1B)) + 0x1BC5) & 0xFFFFFFFF
right    = (((s2 << (row & 3)) & 0xFFFFFFFF) + 0x2048) & 0xFFFFFFFF
rotation = (left | right) % (N - 1)
```

Undo the per-row rotation modulo `N - 1`, then add `old_symbol_count - 1` so each `r_info` references its merged `.dynsym` slot.
{% endstep %}

{% step %}
## Classify the five omitted `libc` PLT holes

CrackProof omits up to five standard `libc` string/memory functions (`strlen`, `strcmp`, `memset`, `strcpy`, `strchr`) from `relocation2`, leaving unreferenced slots in `.got.plt` (after its `0x18`-byte header). Restoration maps each hole to `.plt + 0x20 + slot * 0x10` (plus any `ADRP X16/X17; ADD; BR` compiler veneers), inspects AArch64 call-site argument registers and return usage across `.text`, appends `SHN_UNDEF` `STT_FUNC` symbols for the matched functions, and emits the missing `R_AARCH64_JUMP_SLOT` (`0x402`) records into `.rela.plt`.
{% endstep %}

{% step %}
## Normalize `.rela.dyn`, rebuild symbol hashes, and recover constructors

Any `.rela.dyn` record (`R_AARCH64_ABS64 = 0x101` or `R_AARCH64_GLOB_DAT = 0x401`) whose target symbol is defined (`st_shndx != SHN_UNDEF`) is converted into `R_AARCH64_RELATIVE` (`0x403`) with `r_addend = st_value + r_addend`. All `R_AARCH64_RELATIVE` entries are sorted by `r_offset` at the front of `.rela.dyn`, and `DT_RELACOUNT` is updated to that prefix length.

Whichever symbol hash sections the input ELF carries (`.gnu.hash`, SysV `.hash`, or both) are rebuilt over the final `.dynsym`. When module `0x98` is present, a bounded AArch64 interpreter executes from `entry_offset` (`X0 = runtime`, `[X0 + 8] = image_base`, expecting `W0 == 1` on `RET`) to recover suppressed constructor pointers, replace the Stage 1 bootstrap slot in `.init_array`, strip `RET`-only (`0xD65F03C0`) placeholders, and update `.init_array`/`.fini_array` section sizes and `DT_INIT_ARRAYSZ`/`DT_FINI_ARRAYSZ`.
{% endstep %}

{% step %}
## Place rebuilt tables in-place or in an appended `PF_R` `PT_LOAD`

If the rebuilt `.dynsym`, `.gnu.version`, hash table(s), `.dynstr`, `.rela.dyn`, and `.rela.plt` fit inside the original file window starting at `.dynsym`, they are written in place. When the expanded tables exceed that window, restoration appends a new read-only (`PF_R`) `PT_LOAD` segment aligned to the maximum `p_align` of existing `PT_LOAD` segments and updates `DT_SYMTAB`, `DT_STRTAB`, `DT_STRSZ`, `DT_GNU_HASH` / `DT_HASH`, `DT_VERSYM`, `DT_RELA`, `DT_RELASZ`, `DT_JMPREL`, and `DT_PLTRELSZ`.

To insert the extra `Elf64_Phdr` without overwriting mapped bytes, reconstruction uses post-PHDR slack when available, reuses a redundant `PT_NOTE` header inside `PT_LOAD` (when two or more `PT_NOTE` headers exist), or moves the program-header table to the start of the appended `PT_LOAD` and updates `e_phoff` and `PT_PHDR`.
{% endstep %}
{% endstepper %}
