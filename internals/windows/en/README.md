---
description: "Internal structures, data transforms, staged reconstruction, and runtime checks of CrackProof-protected Windows PE files."
icon: desktop
---

# CrackProof for Windows internals

CrackProof for Windows protects PE32 (`0x10B`) and PE32+ (`0x20B`) executables and DLLs. A protected binary retains a valid outer PE shell that maps a bootstrap loader, while original application sections, loader stages, import/CLR metadata, and code pages are stored in encrypted and compressed form. At load time, the runtime checks the host environment, reconstructs the memory image, optionally seals executable pages behind a fault handler, and transfers control to the original entry point.

Observed builds span native and managed (.NET) EXEs and DLLs, marker-based and marker-less 64-bit shells, standard and compact 32-bit shells, dedicated 64-bit DLL containers, and PE32+ modules split across a 4 KiB stub and an external `._` companion file.

## Conventions

* Offsets are hexadecimal byte offsets from the start of the file unless stated otherwise. `u32@X` denotes the little-endian 32-bit unsigned integer at offset `X`.
* **RVA** (relative virtual address) follows standard PE usage. Reconstruction operates on an RVA-indexed image buffer (`VirtualAddress == PointerToRawData` on 64-bit outputs; compacted back to `0x200` file alignment on 32-bit outputs).
* Integer operations use fixed-width 8-bit or 32-bit unsigned wraparound matching x86 semantics; Python snippets apply explicit bitmasks (`& 0xFF`, `& 0xFFFFFFFF`).
* `info[0..7]` denotes the eight 32-bit words decoded from file offset `0x1000` (see [Container and encrypted header](file-structure/container-layout.md)).

## Sections

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-folder-tree"></i></td><td><strong>File structure</strong></td><td>On-disk container split at <code>0x1000</code>, <code>KONN</code> header KDF, build families, and external <code>._</code> companions.</td><td><a href="file-structure/file-format.md">Protected file structure</a></td></tr><tr><td><i class="fa-shuffle"></i></td><td><strong>Data transforms</strong></td><td>Rolling XOR and rotation ciphers, LFSR, string and page scrambles, CRC/stage keys, AES-CBC, Huffman/LZ, and bytecode VM.</td><td><a href="data-transforms/data-transforms.md">Data transforms</a></td></tr><tr><td><i class="fa-stairs"></i></td><td><strong>Loading and section recovery</strong></td><td>Nine-phase 64-bit stage chain, PE32 standard/compact and dedicated DLL variants, and marker-less structural discovery.</td><td><a href="loading-and-pe-repair/loading/README.md">Loading and section recovery</a></td></tr><tr><td><i class="fa-puzzle-piece"></i></td><td><strong>PE reconstruction</strong></td><td>Section headers, transient EP/directory blocks, imports and <code>.kmiat</code>, TLS, exports, relocations, and CLR overlays.</td><td><a href="loading-and-pe-repair/pe-reconstruction/README.md">PE reconstruction</a></td></tr><tr><td><i class="fa-play"></i></td><td><strong>Runtime</strong></td><td>Status logging, <code>AAA-BBB-CCC</code> failure codes, anti-analysis checks, <code>KiUserExceptionDispatcher</code> page protection, helpers, and <code>Htsysm</code> drivers.</td><td><a href="runtime/runtime.md">Runtime behavior</a></td></tr><tr><td><i class="fa-compass"></i></td><td><strong>Analysis</strong></td><td>Static vs runtime workflow, observed limitations, <code>-GMD</code> IL2CPP metadata remapping, and master offset/constant tables.</td><td><a href="analysis/analysis.md">Analysis notes</a></td></tr></tbody></table>

Runnable Python implementations and test vectors for the transforms in this section live in [Verification & reference](https://app.gitbook.com/s/8S0xnfw9UP9A2yylicaA/). The 3-byte Huffman/LZ token encoding and in-buffer AES schedule also appear in [CrackProof for Android SO internals](https://app.gitbook.com/s/fcBZibCo72OSh5jVcKoo/).
