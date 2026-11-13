---
description: "Restore seeded five-round MethodDef RID permutations (v29/v31/v39) and v24.1 methodIndex tables."
icon: hashtag
---

# Method tokens

Standard IL2CPP metadata files start with sanity magic `0xFAB11BAF` followed by a 32-bit version number. On Android, CrackProof applies a seeded five-round mirror-and-subtract permutation to per-image `MethodDef` RIDs (`0x06000000 | rid`) in versions `29`, `31`, and `39`, and to global `methodIndex` entries (paired with a 256-entry exception table) in version `24` (`v24.1`). Some version `31` builds instead use the keyless `-GMD` token layout.

For comparison with the keyless Windows `-GMD` remap (which replaces sparse tokens with `0x06000000 | (local_index + 1)` from table order alone), see [il2cpp metadata obfuscation](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/analysis/il2cpp-metadata).

## Five inverse rounds

Given a contiguous range of `count` entries (`count >= 2`) and 32-bit `seed`, derive `key = (seed % (count // 2)) + (count // 4)` and `mirror = count * 2 - 1`. Each zero-based offset `value` (`0 <= value < count`) is inverted in five identical rounds using unsigned 32-bit wraparound (`MASK32 = 0xFFFFFFFF`):

```text
repeat 5 times:
    if value & 1:
        value = mirror - value
    value >>= 1
    if value >= count:
        value = mirror - value
    value = (value - key) & MASK32
    if value > count:
        value = (value + count) & MASK32
```

For `MethodDef` tokens on versions `29`, `31`, and `39`, `value = rid - low` within each image's inclusive RID interval `[low, high]`, and the restored token is `0x06000000 | (value + low)`. Because canonical metadata already has sequential RIDs `1..=count` per image, restoration checks whether an image is already canonical first so clean inputs remain untouched.

## Version-specific layouts and seed recovery

{% tabs %}
{% tab title="Versions 29 & 31" %}
Versions `29` and `31` use fixed header `{offset, size}` pairs and share their type and image descriptors:

* **Types (`@0xA0`, stride `0x58`):** `methodStart` (`u32` at `+0x24`), `method_count` (`u16` at `+0x40`).
* **Images (`@0xA8`, stride `0x28`):** `typeStart` (`u32` at `+0x08`), `typeCount` (`u32` at `+0x0C`).
* **Methods (`@0x30`):**
  * **Version 29:** stride `0x20`, `token` (`u32`) at `+0x14`.
  * **Version 31:** stride `0x24`, `token` (`u32`) at `+0x18`.

At runtime, module `0x0C` hooks `mmap` and applies its embedded seed (`0xA6FAE968` on observed default builds). Static restoration does not require `0x0C` for versions `29`, `31`, or `39`: each image has `count / 2` possible `key` residues, so testing candidates for canonical `1..=count` output order and intersecting the `seed % (count / 2)` constraints across images recovers a valid seed directly from `global-metadata.dat`. Unconstrained files default to `0xA6FAE968`, and version `31` builds protected with `-GMD` use the structural `0x06000000 | (local_index + 1)` remap instead.
{% endtab %}

{% tab title="Version 39 (compact directory)" %}
Version `39` replaces fixed header offsets with a compact directory of 12-byte `{offset, size, count}` section descriptors and variable-width table indices:

* Widths for `type_definition`, `parameter`, and `generic_container` indices are `1` byte (`count <= 255`), `2` bytes (`count <= 65535`), or `4` bytes (`count > 65535`).
* Width for `type_index` is derived from section `18` (`interface_offsets`): `4` bytes when `count == 0`, otherwise `(size / count) - 4`.

Record strides and field offsets for methods, types, and images are computed from those four index widths, after which the same per-image residue discovery and five-round RID inverse run unchanged.
{% endtab %}

{% tab title="Version 24.1 (methodIndex + 0x0C)" %}
External version-`24` metadata matching the `v24.1` `Il2CppMethodDefinition` layout (stride `0x34`, signed `i32` `methodIndex` at `+0x14`) leaves `MethodDef` tokens untouched and instead permutes all non-negative `methodIndex` entries (`0..active_count`, where `active_count > 256`):

1. All `active_count` non-negative `methodIndex` slots are permuted with the five-round function using `key = (seed % (active_count // 2)) + (active_count // 4)`.
2. Values for the first 256 active slots are stored separately in a 256-entry `u32` exception table inside module `0x0C`.

Static restoration therefore pairs the metadata file with the owning application's decoded module `0x0C`, locates the `{u32 seed, u32 24}` and `{u32 1, u32 active_count - 1}` header markers plus the 256-entry exception table inside `0x0C`, restores the 256 exception entries, and inverts the five-round permutation across all `active_count` active methods.
{% endtab %}
{% endtabs %}

## Post-restoration checks

After remapping, validation verifies that image, type, and method tables fit inside the file, every method belongs to exactly one image in contiguous table order, every `MethodDef` token carries table prefix `0x06000000` with canonical local RIDs (or `0..active_count` coverage on `v24.1`), and no out-of-range or duplicate entries remain.
