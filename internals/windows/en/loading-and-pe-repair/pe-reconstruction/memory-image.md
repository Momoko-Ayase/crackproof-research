---
description: "How protected section headers describe a memory image and which PE fields are restored."
---

# Headers, sections, and zero-fill ranges

Encryption of the section content is only half of what the packer does. The PE structure itself is dismantled: fields the Windows loader needs are removed or encrypted, and the runtime loader re-creates them after unpacking. This page catalogues each transformation and its runtime counterpart. It matters for two audiences: anyone analyzing a protected file statically (the structures are not where PE tooling expects them), and anyone validating a reconstructed image (each transformation has a corresponding restoration step that must have happened).

## Section headers become a memory layout

A normal PE maps file offsets to RVAs through the section table. A protected image instead stores the layout the loader produces in memory: each section's `SizeOfRawData` is set to its `VirtualSize`, and `PointerToRawData` to its `VirtualAddress`. Section content is then addressed uniformly by RVA, on disk and in memory alike.

The 32-bit family adds the inverse transformation as its last step: the RVA-laid image is compacted back into a file-aligned PE — headers at `0x400`, sections packed consecutively at `0x200` file alignment, trailing zero runs trimmed from each section's raw data, and `FileAlignment`/`SizeOfHeaders` rewritten.

## The entry point and data directories are encrypted

`AddressOfEntryPoint` and all sixteen `IMAGE_DATA_DIRECTORY` entries are stored encrypted near the image base (`info[3]`), wrapped in the [position-keyed byte cipher](../../data-transforms/rolling-and-rotation.md#triple-byte-rotation-ciphers). Two placements exist per bitness:

| Family | Block start | Entry point | Directories | Encrypted size |
| --- | --- | --- | --- | --- |
| 64-bit, "Layout A" (marker layout) | `info[3] + 0x40` | `+0x40` | `+0x50` | 144 bytes |
| 64-bit, "Layout B" (marker-less) | `info[3] + 0x20` | `+0x20` | `+0x30` | 144 bytes |
| 32-bit, "Layout A" | `info[3] + 0x40` | `+0x40` | `+0x50` | 144 bytes |
| 32-bit, "Layout B" | `info[3] + 0x10` | `+0x20` | `+0x30` | 0x290 bytes |

On 64-bit marker builds the placement is probed: trial-decrypt the dword after the candidate entry point and check whether it matches the image base. On 32-bit the selector is the dword at `info[3] + 0x10` (above `0x10000` → Layout B). The block is decrypted **transiently** — entry point to `pe + 40`, the 128 directory bytes to `pe + 136` (64-bit) or `pe + 0x78` (32-bit) — and the encrypted bytes are then restored: the protected file keeps this region encrypted even after everything else is unpacked, so a correct reconstruction still shows ciphertext at `info[3] + ep_off`.

The PE header fields the runtime loader does not use directly stay blanked in the on-disk header until this restoration runs — which is why PE tooling shows a garbage entry point (a common small value like `0x1B5C`) on a protected file.

Managed images store 0 as the entry point in this block. The real entry is a property of the CLR header, not the PE. Reconstruction keeps the protected header's entry point when the decrypted value is 0; writing 0 would point the image at the DOS header.

## The zero-fill lists

Not every region of the original image is stored: `.bss`-style regions are delivered as zero-fill lists — walk4's second chain on 64-bit, the zero-list cluster slot on 32-bit, and a trailing zero-fill chain in the dedicated DLL layout. Each entry is a `(dst, size)` pair, decrypted with the same 16-byte positional chain as the section descriptors, and zeroed after (32-bit: before) decompression.

