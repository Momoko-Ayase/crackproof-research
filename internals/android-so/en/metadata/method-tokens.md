---
description: "Identify IL2CPP metadata version 31 and validate per-image method ranges."
---

# Method tokens

The recognized IL2CPP metadata magic is `0xFAB11BAF`; the documented version is `31`. A MethodDef token has table byte `0x06` in the high byte and a row identifier in the low 24 bits.

For each native image, the protected method block is represented by a contiguous RID interval. The intervals must be non-overlapping, cover the declared method records, and form a permutation of the expected image order. A token outside its interval or a duplicate RID is rejected.

The method bytes use five inverse rounds and a per-image seed. The seed is taken from the protected record, not inferred from a neighboring method. After restoration, the metadata header, table offsets, string ranges, and method-token references are checked again.

Cleaning is idempotent: applying the cleanup pass to already clean metadata leaves the bytes unchanged and does not create a second header or table.
