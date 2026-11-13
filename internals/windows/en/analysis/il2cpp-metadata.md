---
description: "Reversing the keyless Windows -GMD sparse MethodDef token obfuscation in Unity il2cpp global-metadata.dat."
icon: table
---

# il2cpp metadata obfuscation

On Unity IL2CPP Windows builds, CrackProof's optional `-GMD` mode modifies `global-metadata.dat` alongside the protected PE (`GameAssembly.dll`), rewriting the `token` field of every `Il2CppMethodDefinition` entry.

## Mechanism and failure symptom

At startup, IL2CPP resolves each method's compiled code pointer and invoker by indexing `Il2CppCodeGenModule.methodPointers` and `invokerIndices` at `(token & 0x00FFFFFF) - 1`. Because those arrays are sized to the module's compiled method count, IL2CPP requires per-module `MethodDef` RIDs to form the contiguous sequence `1..=methodPointerCount`.

`-GMD` replaces those contiguous RIDs with sparse ECMA-335-style tokens (for example, RIDs reaching `~55,000` inside a module with `~14,000` compiled methods). Inside the protected process, CrackProof's runtime remaps them before IL2CPP reads them; if `GameAssembly.dll` is unpacked statically without restoring `global-metadata.dat`, `(token_row - 1)` indexes out of bounds during `il2cpp_init` (typically crashing with `0xC0000005` while initializing `System.Array` interface methods).

## Keyless structural restoration

Because `Il2CppMethodDefinition` rows are stored grouped contiguously by declaring type (`Il2CppTypeDefinition`), and types are grouped contiguously by module (`Il2CppImageDefinition`), each method's canonical token is determined purely by table order with no key required:

```text
local_index = method_index - image_first_method_index
new_token   = 0x06000000 | ((local_index + 1) & 0x00FFFFFF)
```

Field and type tokens are already canonical and stay untouched. On an unobfuscated `global-metadata.dat`, `new_token` equals the existing `token`, making the transform idempotent.

## Version-31 layout constants

| Item | Value |
| --- | --- |
| Sanity magic (`+0x00`) | `0xFAB11BAF` |
| Metadata version (`+0x04`) | `31` |
| Header `{offset, size}` pairs | `methods @0x30`, `types @0xA0`, `images @0xA8` |
| Record strides | `method = 0x24`, `type = 0x58`, `image = 0x28` |
| Key fields | `method.token` (`u32` at `+0x18`); `type.methodStart` (`u32` at `+0x24`), `type.method_count` (`u16` at `+0x40`); `image.typeStart` (`u32` at `+0x08`), `image.typeCount` (`u32` at `+0x0C`) |

Always verify `0xFAB11BAF`, `version == 31`, in-file table bounds, exact stride divisibility, and contiguous single-image method ownership before writing restored bytes. Android IL2CPP builds use a seeded five-round RID or `methodIndex` permutation restored by module `0x0C` (with `-GMD` as a fallback on version 31); see [Method tokens](https://app.gitbook.com/s/fcBZibCo72OSh5jVcKoo/metadata/method-tokens).
