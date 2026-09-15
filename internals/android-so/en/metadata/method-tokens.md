---
description: "Identify supported IL2CPP metadata versions and restore per-image method RID permutations."
---

# Method tokens

The recognized IL2CPP metadata magic is `0xFAB11BAF`. Versions 29, 31, and 39 are supported layouts, and all three share the seeded five-round RID permutation in [Five inverse rounds](#five-inverse-rounds). A MethodDef token has table byte `0x06` in the high byte and a row identifier in the low 24 bits.

This isn't the Windows `-GMD` remap. Windows replaces each token with the contiguous `0x06000000 | (local_index + 1)` value derived from table order alone. The Android path is a seeded five-round permutation of the RID inside each image's method block. See [il2cpp metadata obfuscation](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/analysis/il2cpp-metadata) for the Windows rule.

## Image intervals

For each native image, the protected method block is a contiguous RID interval. The intervals must be non-overlapping, cover the declared method records, and form a permutation of the expected image order. A token outside its interval or a duplicate RID is rejected.

The seed is taken from the protected record (module `0x0C`), not inferred from a neighboring method. One observed default is `0xa6fae968`. After restoration, the metadata header, table offsets, string ranges, and method-token references are checked again.

On IL2CPP libraries the same cleanup also runs at load time: module `0x0C` replaces `mmap` with a hook and restores tokens when the process maps `global-metadata.dat`. Native libraries in the same family don't carry `0x0C`. See [Runtime modules](../runtime/modules.md).

## Five inverse rounds

Let `low`/`high` be the inclusive RID bounds of one image, `count = high - low + 1` (`count ≥ 2`), and `key = (seed % (count / 2)) + count / 4`. For an encrypted RID `rid`:

```
value = rid - low
repeat 5 times:
    mirror = count * 2 - 1
    if value is odd: value = mirror - value
    value >>= 1
    if value >= count: value = mirror - value
    value = value - key          (mod 2^32 wrap)
    if value > count: value = value + count
rid' = value + low
```

The new token is `0x06000000 | rid'`. The transform is idempotent: an image whose tokens are already in canonical per-image order is left untouched rather than having the inverse applied a second time.

Table constants differ by version. Versions 29 and 31 share the type and image layouts with the Windows version-31 table: types `@0xA0` stride `0x58`, images `@0xA8` stride `0x28`; type `.methodStart +0x24` / `.method_count +0x40`, image `.typeStart +0x08` / `.typeCount +0x0C`. They differ only in the method row:

| Version | Method table | Method stride | `.token` offset |
| --- | --- | --- | --- |
| 29 | `@0x30` | `0x20` | `+0x14` |
| 31 | `@0x30` | `0x24` | `+0x18` |

Version 39 replaces the fixed header with a table of 12-byte `(offset, size, count)` section records and variable-width indexes (1, 2, or 4 bytes, chosen from each table's count). Its method, type, and image strides are derived from those widths. Any other version is rejected rather than decoded with the wrong layout.
