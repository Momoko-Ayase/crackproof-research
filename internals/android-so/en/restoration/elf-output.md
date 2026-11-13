---
description: "Finalize clean ELF64 section headers, clear e_entry, write the output atomically, and verify the restored binary."
icon: file-export
---

# ELF output

Once the `PT_LOAD` segments and dynamic-linking tables are rebuilt, ELF finalization removes protection-only structures and rewrites the non-allocatable tail of the file:

1. **Remove `SHT_LOUSER`:** the trailing private section header is dropped, and none of the Stage 1/2 payload bytes are copied into the output file.
2. **Clear `e_entry` to `0`:** Android shared libraries run native constructors through `.init_array` rather than `e_entry`, so `e_entry` is zeroed.
3. **Relocate non-`SHF_ALLOC` sections:** retained non-allocatable sections (such as `.shstrtab`) are packed after the end of the loadable segments (including any appended `PF_R` `PT_LOAD`), `.shstrtab` is validated, and the updated `Elf64_Shdr` table is written at the end with `e_shoff` and `e_shnum` updated.
4. **Write atomically and re-parse:** outputs written to disk go through a temporary file before atomic rename, then are re-parsed from the written bytes.

{% hint style="info" %}
**Hard post-write checks vs structural diagnostics.** Output validation distinguishes two tiers:
* **Hard errors (abort restoration):** ELF64 little-endian AArch64 parse failure, `PT_LOAD` file ranges exceeding the output length, malformed `.shstrtab`, a surviving `SHT_LOUSER` section, non-zero `e_entry`, or `.dynsym` / `.rela.dyn` / `.rela.plt` counts disagreeing with the rebuilt tables.
* **Cross-table diagnostics (reported as warnings):** linker-walk checks over `PT_LOAD` alignment/congruence/overlap, `DT_*` tag vs section agreement, `DT_RELACOUNT` prefix ordering, symbol-hash bucket bounds, relocation target/symbol bounds, and `.init_array` / `.fini_array` function pointers.
{% endhint %}
