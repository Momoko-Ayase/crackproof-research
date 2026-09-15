---
description: "How import names, TLS state, and exported data are recovered from different protected layouts."
---

# Imports, TLS, and exports

## Imports: encrypted names, rebuilt tables

Import names (DLL names and by-name function names) are encrypted with the [string cipher](../../data-transforms/lfsr-strings-pages.md#the-import-name-string-cipher), keyed by the low byte of each string's own RVA. The reconstruction walks differ by family but share the same finishing rules:

- Each name is decrypted in place and lowercased.
- By-name thunks have their hint/name string decrypted and the 2-byte hint field zeroed. Ordinal thunks (top bit set — bit 63 on PE32+, bit 31 on PE32) are skipped. Reading only the low dword of a PE32+ thunk would mistake an ordinal for a tiny RVA and corrupt the header — the 8-byte width matters.
- The IAT data directory (entry 12) bounds are recovered by tracing the first thunks.

The table source differs:

- **Marker layout (64-bit):** the walk5 encrypted-pointer table inside stage 5. A null walk5 pointer means there is no table to walk — managed assemblies leave the slot empty because their imports are the CLR bootstrap stub.
- **Marker-less layout:** the PE import directory itself, driven by `DataDirectory[1]` — with a fallback to the anchor-stage import directory when the metadata's is zero (common on managed images). Name decryption runs after the code-page scramble, because the import strings live inside `.text` on these builds.
- **Dedicated DLL layout:** in-place decryption of the existing table.
- **32-bit:** the EighthStage import table, or the metadata directory's when it validates better.

**The `.kmiat` relocation (32-bit EXEs).** When the loader-written IAT does not match the original `.idata` layout, the import metadata (descriptors, lookup tables, name pool) is rebuilt into the last section, renamed `.kmiat`, sized `0x7000`, characteristics `0xE0000060`; the live IAT stays at its original RVA and the import directory is repointed. `api-ms-win-crt-*` names normalize to `ucrtbase.dll`. DLLs skip this — they keep their real import table.

## TLS is stripped and reinstalled at runtime

The packer removes the entire `IMAGE_TLS_DIRECTORY`: the data-directory entry, the struct, and the raw-data template. The runtime loader reinstalls TLS itself when it maps the module. The base relocations covering the struct's pointer fields don't survive intact either: 64-bit payloads drop them, and 32-bit DLLs keep the four entries only in neutralized form — demoted to `IMAGE_REL_BASED_ABSOLUTE` but with their original offsets preserved, where genuine padding keeps offset 0 — because the packer's loader fixes TLS up by hand.

A statically reconstructed image does not get that treatment — the ordinary Windows loader needs a valid TLS directory, or it never allocates a TLS slot and never writes `_tls_index`. Every C++ `thread_local` access then resolves through a garbage slot and the module faults during initialization (`0xC0000005` deep in runtime init). The genuine directory survives in plaintext in the loader stub's `.rdata`/`.tls` (single-file builds keep it in the protected file; the companion layout keeps it in the stub), so reconstruction overlays the struct and the raw-data template byte-for-byte at their RVAs and restores the relocations covering the struct's pointer fields. On 64-bit builds that means appending `DIR64` entries for the four 64-bit fields; on 32-bit DLLs the four slots are already present and are re-armed to `IMAGE_REL_BASED_HIGHLOW` — left neutralized, a DLL mapped off its preferred base keeps a stale `AddressOfIndex`, and the OS loader faults in `LdrpAllocateTlsEntry` while writing the TLS slot index through it. Older single-file builds predate this stripping and have no TLS directory at all.

## Exports survive in plaintext — elsewhere

The export directory is never encrypted in the payload. Where it lives depends on the layout:

- **Single-file layouts:** the export region sits in plaintext in the protected file at its RVA; the loader copies it into the image as-is. (The region is found from `DataDirectory[0]`, readable from the plaintext header.)
- **External-companion layout:** the companion decrypts to garbage in the export area (`NumberOfFunctions` and friends are ciphertext). The runtime loader rebuilds exports from the plaintext copy retained in the stub's `.rdata`. A static reconstruction must likewise overlay the export-directory region from the stub, or analysis tools choke on the export table.

