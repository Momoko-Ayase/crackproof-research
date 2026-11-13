---
description: "RVA-aligned section headers, 32-bit file compaction, transient EP/directory decryption, and .bss zero-fill chains."
icon: memory
---

# Headers, sections, and zero-fill ranges

In addition to encrypting section bytes, CrackProof clears or redirects PE header fields (`AddressOfEntryPoint`, selected `IMAGE_DATA_DIRECTORY` entries, and section raw pointers) and restores them in memory during startup.

## RVA-mapped section headers and 32-bit compaction

On 64-bit outputs (and during working-buffer recovery on 32-bit), section headers are normalized to memory layout so file offsets equal RVAs:

* `SizeOfRawData = VirtualSize`
* `PointerToRawData = VirtualAddress`

On 32-bit (`PE32`) outputs, a final compaction pass converts that RVA buffer back into a compact disk-aligned PE: headers end at `0x400`, sections pack sequentially on `0x200` (`FileAlignment`) boundaries with trailing zero padding trimmed from `SizeOfRawData`, and `SizeOfHeaders` / `FileAlignment` are updated accordingly.

## Transient entry-point and data-directory block

`AddressOfEntryPoint` and the 16 `IMAGE_DATA_DIRECTORY` entries (128 bytes) live near `info[3]` encrypted with `byte_rotate2`:

| Family & variant | Block start | Entry point offset | Directories offset | Encrypted length |
| --- | --- | --- | --- | --- |
| 64-bit Layout A (marker) | `info[3] + 0x40` | `+0x40` | `+0x50` | `144` (`0x90`) bytes |
| 64-bit Layout B (marker-less) | `info[3] + 0x20` | `+0x20` | `+0x30` | `144` (`0x90`) bytes |
| 32-bit Layout A | `info[3] + 0x40` | `+0x40` | `+0x50` | `144` (`0x90`) bytes |
| 32-bit Layout B (standard shell) | `info[3] + 0x10` | `+0x20` | `+0x30` | `0x290` bytes |
| 32-bit Layout B (compact shell) | `info[3] + 0x10` | `+0x30` | `+0x40` | `0x290` bytes |

* **Variant detection:** 64-bit marker builds probe whether the decrypted dword right after the candidate entry point equals `ImageBase`; 32-bit builds select Layout B when decrypted `u32@(info[3] + 0x10) > 0x10000` (using `+0x30` / `+0x40` on compact `tbl` shells). Dedicated 64-bit DLLs instead read a 656-byte `byte_rotate2` blob at `info[3] + 16` (`EntryPoint` at `+0x10`, directories at `+0x20`).
* **Transient decryption:** the block is decrypted to copy `AddressOfEntryPoint` to `pe + 40` and the 128 directory bytes to `pe + 136` (PE32+) or `pe + 0x78` (PE32), then **restored to its encrypted bytes at `info[3]`** so the loader workspace retains its original bytes.
* **Zero entry points on managed images:** managed assemblies store `0` as `AddressOfEntryPoint` in this block. On 64-bit marker and 32-bit builds, reconstruction keeps the outer PE header's `_CorExeMain` / `_CorDllMain` stub entry point whenever the decrypted value is `0`; marker-less 64-bit and dedicated 64-bit DLL builds write `0` directly (valid for pure-IL managed DLLs).

## `.bss` zero-fill chains

Uninitialized ranges omitted from compressed section blocks are supplied by a separate 16-byte `byte_rotate2`-encrypted `{dst, size}` chain (the second `walk4` chain on 64-bit, cluster `+0x48` on 32-bit, and the trailing chain on dedicated 64-bit DLLs). Ranges are zeroed after section decompression on 64-bit builds and before decompression on 32-bit builds.
