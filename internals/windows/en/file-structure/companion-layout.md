---
description: "How section payloads are located and how stub executables refer to external companion files."
---

# Section data and companion files

## Locating section data in the file

Section-content descriptors inside the loader tables store offsets relative to a base that is itself complement-encoded in the file at offset `0x1080`:

```
section_data_file_base = (~u32@0x1080) + 0x1000      (32-bit wrapping)
```

A descriptor's `src` field therefore maps to file offset `src + section_data_file_base`. The same formula appears in every build family (it is referenced as both `rebase` and `compress_data_offset` in loader code).

## The external-companion layout (`._` files)

Some builds — observed so far on il2cpp titles — split a protected module into two files:

- **`Foo.dll`** — a thin on-disk **loader stub**. Its code sections are stripped down to a single page (the CrackProof loader itself), but its headers and `.rdata` are intact plaintext.
- **`Foo.dll._`** — the encrypted **companion**, holding the real payload. It contains no plaintext PE structures at all (entropy ≈ 8 bits/byte).

The companion is byte-for-byte the stub's payload region starting at the CrackProof header (offset 4096) onward. At runtime the loader maps `Foo.dll._` and runs the ordinary unpack over it; the module that runs is effectively the splice `stub[..4096] ++ companion`.

The pairing is confirmed by a 32-byte exact match: `stub[4096..4128] == companion[0..32]`. These 32 bytes cover the encrypted info header (key table and magic), so a match proves the companion is this stub's payload and not an unrelated file.

What the stub retains in plaintext matters for later reconstruction:

- The **export directory** (the companion decrypts to ciphertext here; the loader rebuilds exports at runtime from the stub's copy).
- The **TLS directory** — the `IMAGE_TLS_DIRECTORY` struct, its raw-data template, and the data-directory entry, all of which the packer strips from the encrypted payload (see [PE transformations](../loading-and-pe-repair/pe-reconstruction/README.md)).
- A real `DllCharacteristics` field and base-relocation table — companion modules are **not** `/FIXED`, unlike the older single-file builds.

For the boot-time view of how this pair is loaded, see [Runtime behavior](../runtime/runtime.md); for how the missing pieces are restored into a reconstructed image, see [PE transformations](../loading-and-pe-repair/pe-reconstruction/README.md).

