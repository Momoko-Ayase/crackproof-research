---
description: "How the CrackProof for Windows protection scheme works internally — protected file format, data transforms, staged loader, runtime behavior."
---

# CrackProof for Windows internals

CrackProof® for Windows® is a commercial software-protection product for Windows PE files (executables and DLLs), developed by HyperTech. The CrackProof family also covers other platforms — Android (DEX and native libraries) and iOS — but those variants are out of scope here: this document analyzes only the Windows PE scheme. The protection is applied to finished binaries after compilation: the original program image is encrypted, compressed, and re-packaged with a loader that reconstructs the program in memory when the file runs. It has shipped on a range of commercial software, including Unity/il2cpp games, native game middleware DLLs, and desktop applications.

This document is a research write-up of **how CrackProof works internally**, produced by static and dynamic analysis of protected binaries and of the loader code they carry. It covers:

- **What a protected file looks like on disk** — the container layout, the encrypted header, and how protected files are recognized and classified.
- **The data transforms** — the family of ciphers, the checksum chaining, the compression format, and the per-build custom byte transform every protected file carries.
- **The staged loader** — how the bootstrapping code is itself split into encrypted stages that decrypt each other in sequence, and how the original program sections are recovered.
- **What the packer does to the PE** — which header fields, tables, and directories are removed, encrypted, or relocated, and what the loader rebuilds at runtime.
- **What a protected binary does when it runs** — environment and anti-analysis checks, kernel drivers, manually mapped submodules, and on-demand page decryption.
- **Observed weaknesses** — places where specific checks or mechanisms fall short, documented for research purposes.

## Legal notice

**Read this before using the information in this document.**

- This document is a research publication. It exists to support lawful security research, preservation, and interoperability with software you legitimately possess, and it documents the protection scheme at the format level.
- **Only analyze binaries you own or are explicitly authorized to analyze.** Depending on your jurisdiction and license agreements, circumventing technological protection measures may be restricted (for example under DMCA §1201 in the United States, which contains exemptions for security research and interoperability). It is your responsibility to ensure your use of this information is lawful.
- This document contains no vendor code, keys, or copyrighted content. Every structure and algorithm described here is the result of original analysis, and the reference implementations are clean-room Python written from that analysis.
- Nothing in this document enables online-play fraud, license fraud, or cheating, and it must not be used to redistribute decrypted binaries of any protected product.
- This is an independent work. It is not affiliated with, endorsed by, or sponsored by HyperTech. CrackProof and Windows are trademarks of their respective owners.
- The authors provide this document "as is", without warranty of any kind, and accept no liability for misuse.

## Conventions

- All offsets are hexadecimal byte offsets from the start of the file unless noted otherwise. `u32@X` means the little-endian 32-bit value at offset X.
- **RVA** (relative virtual address) is used in the usual PE sense. The loader works on a memory image laid out by RVA; on disk the same offsets are used as file offsets into the unpacked image buffer.
- Integer arithmetic is fixed-width (32-bit or 8-bit) with wraparound, matching the x86 environment the algorithms come from. The Python reference code applies explicit masks for this.
- Names like `info[3]` refer to entries of the 8-dword table derived from the encrypted file header (see [The protected file format](file-format.md)).

## Reading map

1. [The protected file format](file-format.md) — container layout, the encrypted header, detection and classification, the external-companion split layout.
2. [Data transformation primitives](primitives.md) — every cipher, the checksum chaining, the block cipher, the Huffman/LZ decompressor, and the per-build bytecode transform, with tested Python implementations.
3. [The staged loader](staged-loader.md) — the stage chain, key derivation across stages, and section recovery for each build family.
4. [PE transformations](pe-transformations.md) — what is stripped, encrypted, or relocated in the PE, and what the loader rebuilds.
5. [Runtime behavior](runtime-behavior.md) — the boot sequence, status codes and logging, anti-analysis checks, page-level encryption, and code obfuscation.
6. [Kernel drivers and submodules](kernel-components.md) — the Htsysm driver generations and the manually mapped helper modules.
7. [Reverse engineering notes](analysis-notes.md) — methodology that worked, and observed weaknesses.
8. [il2cpp metadata obfuscation](il2cpp-metadata.md) — the optional method-token obfuscation for Unity il2cpp titles.
9. [Appendix: constants and offsets](appendix.md) — quick-reference tables.
