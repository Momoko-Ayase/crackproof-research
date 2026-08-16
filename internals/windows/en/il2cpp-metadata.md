---
description: "The optional -GMD method-token obfuscation applied to Unity il2cpp titles' global-metadata.dat."
---

# il2cpp metadata obfuscation

Separate from the PE protection, CrackProof offers an option (`-GMD`) that obfuscates Unity il2cpp titles' **`global-metadata.dat`**. It changes exactly one thing: the **method-token field** of every `Il2CppMethodDefinition` record.

## What it does and why it works

il2cpp resolves a method's compiled function and invoker by indexing the per-module `Il2CppCodeGenModule.methodPointers` / `invokerIndices` tables — sized to the module's *compiled* method count — by `(token_row - 1)`. That indexing is only valid when each module's method tokens are the **contiguous** range `1..=methodPointerCount`.

`-GMD` replaces the contiguous tokens with sparse, original-.NET-metadata-style values (in one observed title, the core library's rows reach ~55,000 for only ~14,000 compiled methods). The running protected game's loader remaps them back at load time, so the game works — but the metadata file on its own is now inconsistent with what il2cpp's runtime expects.

This matters whenever the metadata is consumed outside the protected loader: an il2cpp image launched without the loader's remapping reads the tokens raw, `(token_row - 1)` runs off the end of the per-module tables, and the process crashes deep in il2cpp initialization (the first casualty is typically `System.Array`'s interface-method setup, surfacing as `0xC0000005`). Analysis tools that parse `global-metadata.dat` see method references pointing at rows that do not exist in the compiled tables.

## Reversal from structure alone

The obfuscation needs no key and carries no secret — which means it is reversible from the metadata's own structure. Methods are laid out grouped by type, and types grouped by image (module), so a method's correct token row is its position within its module's method range:

```
local_index = method_index - module_first_method_index
new_token   = 0x06000000 | ((local_index + 1) & 0x00FFFFFF)
```

Only method tokens need this treatment: field tokens are already contiguous, and type tokens resolve correctly. The transform is **idempotent** — on unobfuscated metadata the computed tokens already equal the stored ones, so applying it is a no-op.

Key format constants (metadata version 31, Unity 2022.3-era):

| Item | Value |
| --- | --- |
| Sanity magic (offset 0) | `0xFAB11BAF` |
| Format version (offset 4) | `31` |
| Header tables (offset/size i32 pairs) | methods `@0x30`, types `@0xA0`, images `@0xA8` |
| Struct strides | method `0x24`, type `0x58`, image `0x28` |
| Fields | method `.token +0x18`; type `.methodStart +0x24`, `.method_count +0x40` (u16); image `.typeStart +0x08`, `.typeCount +0x0C` |

Other metadata versions use different struct strides and must be handled per-version; applying the version-31 layout to an unknown version corrupts the file, so any implementation should validate magic, version, and exact table divisibility before writing a single byte.
