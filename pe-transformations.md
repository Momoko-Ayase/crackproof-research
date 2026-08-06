---
description: "What Crackproof removes, encrypts, or relocates in the PE structure, and what the loader rebuilds at runtime."
---

# PE transformations

Encryption of the section content is only half of what the packer does. The PE structure itself is dismantled: fields the Windows loader needs are removed or encrypted, and the runtime loader re-creates them after unpacking. This page catalogues each transformation and its runtime counterpart. It matters for two audiences: anyone analyzing a protected file statically (the structures are not where PE tooling expects them), and anyone validating a reconstructed image (each transformation has a corresponding restoration step that must have happened).

## Section headers become a memory layout

A normal PE maps file offsets to RVAs through the section table. A protected image instead stores the layout the loader produces in memory: each section's `SizeOfRawData` is set to its `VirtualSize`, and `PointerToRawData` to its `VirtualAddress`. Section content is then addressed uniformly by RVA, on disk and in memory alike.

The 32-bit family adds the inverse transformation as its last step: the RVA-laid image is compacted back into a file-aligned PE — headers at `0x400`, sections packed consecutively at `0x200` file alignment, trailing zero runs trimmed from each section's raw data, and `FileAlignment`/`SizeOfHeaders` rewritten.

## The entry point and data directories are encrypted

`AddressOfEntryPoint` and all sixteen `IMAGE_DATA_DIRECTORY` entries are stored encrypted near the image base (`info[3]`), wrapped in the [position-keyed byte cipher](primitives.md#triple-byte-rotation-ciphers). Two placements exist per bitness:

| Family | Block start | Entry point | Directories | Encrypted size |
| --- | --- | --- | --- | --- |
| 64-bit, "Layout A" (marker layout) | `info[3] + 0x40` | `+0x40` | `+0x50` | 144 bytes |
| 64-bit, "Layout B" (marker-less) | `info[3] + 0x20` | `+0x20` | `+0x30` | 144 bytes |
| 32-bit, "Layout A" | `info[3] + 0x40` | `+0x40` | `+0x50` | 144 bytes |
| 32-bit, "Layout B" | `info[3] + 0x10` | `+0x20` | `+0x30` | 0x290 bytes |

On 64-bit marker builds the placement is probed: trial-decrypt the dword after the candidate entry point and check whether it matches the image base. On 32-bit the selector is the dword at `info[3] + 0x10` (above `0x10000` → Layout B). The block is decrypted **transiently** — entry point to `pe + 40`, the 128 directory bytes to `pe + 136` (64-bit) or `pe + 0x78` (32-bit) — and the encrypted bytes are then restored: the protected file keeps this region encrypted even after everything else is unpacked, so a correct reconstruction still shows ciphertext at `info[3] + ep_off`.

The PE header fields the runtime loader does not use directly stay blanked in the on-disk header until this restoration runs — which is why PE tooling shows a garbage entry point (a common small value like `0x1B5C`) on a protected file.

## Imports: encrypted names, rebuilt tables

Import names (DLL names and by-name function names) are encrypted with the [string cipher](primitives.md#the-import-name-string-cipher), keyed by the low byte of each string's own RVA. The reconstruction walks differ by family but share the same finishing rules:

- Each name is decrypted in place and lowercased.
- By-name thunks have their hint/name string decrypted and the 2-byte hint field zeroed. Ordinal thunks (top bit set — bit 63 on PE32+, bit 31 on PE32) are skipped. Reading only the low dword of a PE32+ thunk would mistake an ordinal for a tiny RVA and corrupt the header — the 8-byte width matters.
- The IAT data directory (entry 12) bounds are recovered by tracing the first thunks.

The table source differs:

- **Marker layout (64-bit):** the walk5 encrypted-pointer table inside stage 5.
- **Marker-less layout:** the PE import directory itself, driven by `DataDirectory[1]` — with a fallback to the anchor-stage import directory when the metadata's is zero (common on managed DLLs). Name decryption runs after the code-page scramble, because the import strings live inside `.text` on these builds.
- **Dedicated DLL layout:** in-place decryption of the existing table.
- **32-bit:** the EighthStage import table, or the metadata directory's when it validates better.

**The `.kmiat` relocation (32-bit EXEs).** When the loader-written IAT does not match the original `.idata` layout, the import metadata (descriptors, lookup tables, name pool) is rebuilt into the last section, renamed `.kmiat`, sized `0x7000`, characteristics `0xE0000060`; the live IAT stays at its original RVA and the import directory is repointed. `api-ms-win-crt-*` names normalize to `ucrtbase.dll`. DLLs skip this — they keep their real import table.

## TLS is stripped and reinstalled at runtime

The packer removes the entire `IMAGE_TLS_DIRECTORY`: the data-directory entry, the struct, the raw-data template, and the base relocations covering the struct's pointer fields. The runtime loader reinstalls TLS itself when it maps the module.

A statically reconstructed image does not get that treatment — the ordinary Windows loader needs a valid TLS directory, or it never allocates a TLS slot and never writes `_tls_index`. Every C++ `thread_local` access then resolves through a garbage slot and the module faults during initialization (`0xC0000005` deep in runtime init). The genuine directory survives in plaintext in the loader stub's `.rdata`/`.tls` (single-file builds keep it in the protected file; the companion layout keeps it in the stub), so reconstruction overlays the struct and the raw-data template byte-for-byte at their RVAs and appends `DIR64` base relocations for the struct's four 64-bit pointer fields. Older single-file builds predate this stripping and have no TLS directory at all.

## Exports survive in plaintext — elsewhere

The export directory is never encrypted in the payload. Where it lives depends on the layout:

- **Single-file layouts:** the export region sits in plaintext in the protected file at its RVA; the loader copies it into the image as-is. (The region is located via `DataDirectory[0]`, readable from the plaintext header.)
- **External-companion layout:** the companion decrypts to garbage in the export area (`NumberOfFunctions` and friends are ciphertext). The runtime loader rebuilds exports from the plaintext copy retained in the stub's `.rdata`. A static reconstruction must likewise overlay the export-directory region from the stub, or analysis tools choke on the export table.

## Relocations and the /FIXED split

Builds differ deliberately in whether the result may be rebased:

- **Older single-file EXE builds are `/FIXED`.** The shell discards the base-relocation table and clears `DllCharacteristics`; the image can only load at its preferred base. A faithful reconstruction mirrors this: `DataDirectory[5]` zeroed, `DllCharacteristics` zeroed.
- **DLLs (any layout) must stay relocatable.** A DLL is almost always mapped away from its preferred base; stripping its relocations makes it unloadable. Reconstruction keeps `DataDirectory[5]` and ensures `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` (`0x0040`) is set.
- **Marker-less and companion builds are not `/FIXED`.** They carry real ASLR flags and a valid relocation table, and any rebase must relocate everything — including the restored TLS directory's pointers, which is why those relocations are appended during TLS restoration.

## The code-page scramble, ordered last

The [per-page scramble](primitives.md#the-per-page-code-scramble) applies to `.text` after section recovery. Ordering constraints observed across families:

- **Marker layout:** scramble runs before the entry-point/data-directory restoration.
- **Marker-less layout:** scramble is deferred until after import-name decryption and is re-selected over the final bytes — and only runs when the entry point falls inside `.text`. Managed DLLs restore their CLR metadata **after** the scramble, because the metadata region lives inside `.text` but is not scrambled code: scrambling it would corrupt roughly one byte per 16 and produce an invalid COR20 signature.
- **32-bit:** the scramble is skipped entirely when the section is already plaintext (native DLLs), detected by comparing the `0xCC`-restoration score against the no-scramble baseline.

## Managed (.NET) structures are preserved, not encrypted

For managed DLLs the COR20 header (`cb == 0x48`) and the BSJB metadata stream survive **verbatim** in the protected file at their RVAs — only the surrounding code is encrypted. Restoration copies both back from the original file (mapped through the protected file's section table), after the code-page scramble. Conversely, when a build blanks the CLR header (a zero-`cb` COR20), the data-directory entry is cleared so the image loads as native rather than being handed to `mscoree!_CorExeMain`, which would crash on the empty header.

Unity il2cpp titles add a second, separate obfuscation outside the PE: method tokens inside `global-metadata.dat`. See [il2cpp metadata obfuscation](il2cpp-metadata.md).

## The zero-fill lists

Not every region of the original image is stored: `.bss`-style regions are delivered as zero-fill lists — walk4's second chain on 64-bit, the zero-list cluster slot on 32-bit, and a trailing zero-fill chain in the dedicated DLL layout. Each entry is a `(dst, size)` pair, decrypted with the same 16-byte positional chain as the section descriptors, and zeroed after (32-bit: before) decompression.

## A note on section characteristics

One subtle non-transformation: the read-only `.rdata` characteristics must survive as-is. Marking `.rdata` writable breaks statically linked MSVC/UCRT images — the CRT's float-format initialization (`_cfltcvt_init`) is gated by a security check that refuses init descriptors in writable sections; skipping it leaves `R6002 - floating point support not loaded` stubs that abort the first `%f` format call. The Windows loader already makes IAT pages temporarily writable while snapping imports, so the original read-only characteristics are sufficient.
