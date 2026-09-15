---
description: >-
  Internal structures and recovery behavior of CrackProof-protected Android
  native libraries.
---

# CrackProof for Android SO internals

This Space describes the Android native-library format used by CrackProof. It focuses on ELF64 little-endian AArch64 files, the private protection section, the staged record streams, and the information needed to reconstruct a usable ELF image.

The format is related to the Windows family but is not a PE variant. Android-specific checks, section names, stream records, and metadata rules are therefore documented separately.

## Contents

| Area                                                  | What it covers                                                                 |
| ----------------------------------------------------- | ------------------------------------------------------------------------------ |
| [File format](file-format/file-format.md)             | ELF recognition, the protected section, and the two-stage stream layout        |
| [Data transforms](data-transforms/data-transforms.md) | Header arithmetic, module configuration, container transforms, and compression |
| [Restoration](restoration/restoration.md)             | Stream dispatch, dynamic linking, and ELF output reconstruction                |
| [Runtime](runtime/runtime.md)                         | Stage 1 bootstrap, the stage 2 interpreter, and runtime module roles           |
| [Metadata](metadata/metadata.md)                      | IL2CPP method tokens and metadata storage variants                             |
| [Analysis](analysis/analysis.md)                      | Validation rules, failure handling, and observed constants                     |

For the Windows PE format, see the [Windows internals Space](https://app.gitbook.com/o/-Lx9XUuXVg8x3nx7ouIX/s/PuKTEy2soDgSB3qfWACy/). The Huffman/LZ token language and an in-buffer AES schedule are shared with that family; the word ciphers, record onion, and helper-library layout are not.
