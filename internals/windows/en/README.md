---
description: "Internal structures and runtime behavior of CrackProof-protected Windows PE files."
---

# CrackProof for Windows internals

CrackProof for Windows protects PE32 and PE32+ executables and DLLs. The protected file retains enough PE structure to load a bootstrap image, while original sections, loader stages, selected directories, names, and code pages are stored in transformed form. The runtime reconstructs the image before transferring control to the original program.

The observed layouts include native and managed images, older marker-based containers, newer layouts that must be identified structurally, and stub executables whose protected payload is stored in a companion file.

## Conventions

- All offsets are hexadecimal byte offsets from the start of the file unless noted otherwise. `u32@X` means the little-endian 32-bit value at offset X.
- **RVA** (relative virtual address) is used in the usual PE sense. The loader works on a memory image laid out by RVA; on disk the same offsets are used as file offsets into the unpacked image buffer.
- Integer arithmetic is fixed-width (32-bit or 8-bit) with wraparound, matching the x86 environment the algorithms come from. The Python reference code applies explicit masks for this.
- Names like `info[3]` refer to entries of the 8-dword table derived from the encrypted file header (see [The protected file format](file-structure/file-format.md)).

## Contents

| Area | Start here |
|---|---|
| On-disk layout and build recognition | [Protected file structure](file-structure/file-format.md) |
| Ciphers, compression, and checksums | [Data transforms](data-transforms/data-transforms.md) |
| Loader stages and section recovery | [Loading and section recovery](loading-and-pe-repair/loading/README.md) |
| Headers, directories, imports, and CLR data | [PE reconstruction](loading-and-pe-repair/pe-reconstruction/README.md) |
| Startup checks, page protection, and kernel components | [Runtime behavior](runtime/runtime.md) |
| Analysis workflow, limitations, and constants | [Analysis notes](analysis/analysis.md) |

Tested code corresponding to the Windows transform pages is published in [Verification and reference](https://app.gitbook.com/s/8S0xnfw9UP9A2yylicaA/readme).
