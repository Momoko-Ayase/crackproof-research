---
description: "The arithmetic, module, container, and compression layers used by Android streams."
---

# Data transforms

The Android format combines a small arithmetic transform for the outer header with module-specific transforms for container records. Compression is a separate layer and is validated by both its input consumption and its output length.

- [Word, stream, and record ciphers](word-and-record.md) cover GF(2³²) mixing and the stream/record heads.
- [Module configuration](module-config.md) is the `0x9B` seed and AES material.
- [Container transforms](container.md) expand `0x9D` segments.
- [Huffman and LZ compression](compression.md) is the writer format, shared with the Windows family.

The pages here describe observable fields and equations. They avoid assigning new names to intermediate states that are not present in the format.
