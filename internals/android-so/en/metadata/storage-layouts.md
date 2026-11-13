---
description: "External global-metadata.dat application pairing and embedded XOR-wrapped slim v24 metadata blobs."
icon: table
---

# Storage layouts

Protected Android IL2CPP builds ship metadata in one of two storage forms:

| Variant | Location | Format after unwrapping |
| --- | --- | --- |
| External `global-metadata.dat` | Standalone file under `assets/bin/Data/Managed/Metadata/` (or split asset APK) | Standard `0xFAB11BAF` header at version `24` (`v24.1`), `29`, `31`, or `39` |
| Embedded slim + XOR blob | `0x2701F30`-byte data blob inside the restored `libil2cpp.so` image | Patched probe dwords `[0x9732CA38, 0xBAC4374F]` rewritten to `[0xFAB11BAF, 24]` |

{% hint style="info" %}
The `metadata_offset` / `metadata_size` fields inside Stage 2 `0x5C` record descriptors hold protector module load, relocation, and import metadata, never IL2CPP `global-metadata.dat`. When matching an external `v24.1` `global-metadata.dat` to module `0x0C`, both files must belong to the same application package (matching `AndroidManifest.xml` `package` and `versionCode`/`versionCodeMajor` across split APKs, or sharing the same `<root>/lib/<abi>/` and `<root>/assets/` tree).
{% endhint %}

## Embedded slim + XOR variant

One older version-`24` packaging variant omits `global-metadata.dat` from `assets/` and embeds a `0x2701F30`-byte XOR-masked blob inside the restored `.so` data section:

* **Structure:** a `0x100`-byte header (64 little-endian `u32` words, one 32-bit XOR key per header word) followed by 256 irregular-length body segments (one 32-bit XOR key per segment, XORed across its dwords).
* **Header probe and fixup:** XORing the first two dwords with `[0x39184C70, 0xD901AFD4]` yields the byte-swapped sentinel pair `[0x9732CA38, 0xBAC4374F]`. Rewriting those two dwords to `[0xFAB11BAF, 24]` after applying the 64 header keys and 256 segment keys produces a valid slim version-24 metadata file.
* **Key derivation status:** at runtime, the metadata loader generates those 320 `u32` keys dynamically; static derivation of the keystream from the `.so` binary alone remains untraced. Newer builds in the same lineage moved to external `global-metadata.dat` files with seeded `MethodDef` permutations.
