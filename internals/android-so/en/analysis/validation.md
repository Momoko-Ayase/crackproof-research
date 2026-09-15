---
description: "A compact validation checklist for protected Android native libraries."
---

# Validation checklist

1. Confirm ELF64 little-endian AArch64 and the expected dynamic sections.
2. Locate exactly one private `SHT_LOUSER` section and bound its file range.
3. Decode stage 1 and check reserved fields, alignment, copied sizes, and image ranges.
4. Parse stage 2 descriptors without crossing a parent stream boundary.
5. Load modules `0x9B`, `0x9D`, and `0x9E`; reject missing or duplicate definitions.
6. Require exact source consumption and target length for every raw or compressed write.
7. Rebuild dynamic-linking tables and verify counts, versions, hashes, and relocations.
8. Validate from disk that the entry point is cleared, the `PT_LOAD` ranges (including any added read-only segment for rebuilt dynamic tables) hold, and the section relationships parse.
9. When metadata is present, check the magic, a supported version (29, 31, or 39, each with its own table layout), table offsets, RID intervals, and idempotent cleanup. Do not apply the Windows `-GMD` remap to an Android token block, and do not decode another version with the version-31 strides.

Any failed item leaves the candidate in an unknown state. It must not be reported as a partially restored library.
