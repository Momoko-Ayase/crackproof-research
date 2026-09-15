---
description: "Rebuild dynamic symbols, version tables, and relocation records from protected streams."
---

# Dynamic linking

The dynamic-linking module restores the information that the Android loader needs after the protected ranges have been expanded.

Module `0x9D` supplies the target and auxiliary containers used to materialize `.dynsym`, `.dynstr`, `.gnu.hash`, `.gnu.version`, `.gnu.version_r`, and relocation tables. The restored offsets and sizes must fit the corresponding `PT_LOAD` range and the file's alignment rules.

Module `0x9E` applies hidden-symbol patches. A patch is accepted only when its symbol index, name offset, version index, and target address point into the restored tables. The symbol count used by the GNU hash table, version arrays, and relocation records must agree; a mismatch is rejected rather than repaired heuristically.

Rebuilt tables are placed in the original file window after `.dynsym` when that window is large enough. On compact images the window is too small, so the restored tables occupy a new read-only `PT_LOAD` appended after the existing load image at the original `PT_LOAD` alignment, and the dynamic tags are updated to the new addresses. Adjacent sections are never overwritten, and a partial table set is never emitted.
