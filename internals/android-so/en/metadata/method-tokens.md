---
description: "Identify IL2CPP metadata version 31 and restore per-image method RID permutations."
---

# Method tokens

The recognized IL2CPP metadata magic is `0xFAB11BAF`; the documented version is `31`. A MethodDef token has table byte `0x06` in the high byte and a row identifier in the low 24 bits.

This is not the Windows `-GMD` remap. Windows replaces each token with the contiguous `0x06000000 | (local_index + 1)` value derived from table order alone. The Android path is a seeded five-round permutation of the RID inside each image's method block. See [il2cpp metadata obfuscation](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/analysis/il2cpp-metadata) for the Windows rule.

## Image intervals

For each native image, the protected method block is a contiguous RID interval. The intervals must be non-overlapping, cover the declared method records, and form a permutation of the expected image order. A token outside its interval or a duplicate RID is rejected.

The seed is taken from the protected record (module `0x0C`), not inferred from a neighboring method. One observed default is `0xa6fae968`. After restoration, the metadata header, table offsets, string ranges, and method-token references are checked again.

On IL2CPP libraries the same cleanup also runs at load time: module `0x0C` replaces `mmap` with a hook and restores tokens when the process maps `global-metadata.dat`. Native libraries in the same family do not carry `0x0C`. See [Runtime modules](../runtime/modules.md).

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

The new token is `0x06000000 | rid'`. Cleaning is idempotent for tooling: an image whose tokens are already the canonical per-image order is detected and left untouched instead of applying the inverse a second time.

Key format constants match the Windows version-31 table (methods `@0x30` stride `0x24`, types `@0xA0` stride `0x58`, images `@0xA8` stride `0x28`; method `.token +0x18`, type `.methodStart +0x24` / `.method_count +0x40`, image `.typeStart +0x08` / `.typeCount +0x0C`). Other metadata versions use different strides and must be rejected rather than decoded with this layout.
