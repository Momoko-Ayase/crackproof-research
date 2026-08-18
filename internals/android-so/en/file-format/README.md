---
description: "Recognize a protected ELF and follow its outer and inner stream boundaries."
---

# File format

The Android format starts with a normal ELF64 little-endian AArch64 file and adds one private section with type `SHT_LOUSER`. The private section contains the protected payload. The normal dynamic-linking sections remain visible and are used during recognition and restoration.

The pages in this group describe the outer header first, then the record stream inside it. Bounds checks are part of the format description because a plausible field is not enough to identify a valid file. Load-time discovery of the same header is in [Stage 1 bootstrap](../runtime/stage1-bootstrap.md).
