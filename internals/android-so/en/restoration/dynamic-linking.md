---
description: "Rebuild dynamic symbols, version tables, and relocation records from protected streams."
---

# Dynamic linking

The dynamic-linking module restores the information that the Android loader needs after the protected ranges have been expanded.

Module `0x9D` supplies the target and auxiliary containers used to materialize `.dynsym`, `.dynstr`, `.gnu.hash`, `.gnu.version`, `.gnu.version_r`, and relocation tables. The restored offsets and sizes must fit the corresponding `PT_LOAD` range and the file's alignment rules.

Module `0x9E` applies hidden-symbol patches. A patch is accepted only when its symbol index, name offset, version index, and target address point into the restored tables. The symbol count used by the GNU hash table, version arrays, and relocation records must agree; a mismatch is rejected rather than repaired heuristically.
