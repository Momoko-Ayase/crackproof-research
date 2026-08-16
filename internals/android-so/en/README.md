---
description: "Internal structures and recovery behavior of CrackProof-protected Android native libraries."
---

# CrackProof for Android SO internals

This Space describes the Android native-library format used by CrackProof. It focuses on ELF64 little-endian AArch64 files, the private protection section, the staged record streams, and the information needed to reconstruct a usable ELF image.

The format is related to the Windows family but is not a PE variant. Android-specific checks, section names, stream records, and metadata rules are therefore documented separately.

## Contents

| Area | What it covers |
| --- | --- |
| [File format](file-format/README.md) | ELF recognition, the protected section, and the two-stage stream layout |
| [Data transforms](data-transforms/README.md) | Header arithmetic, module configuration, container transforms, and compression |
| [Restoration](restoration/README.md) | Stream dispatch, dynamic linking, and ELF output reconstruction |
| [Metadata](metadata/README.md) | IL2CPP method tokens and metadata storage variants |
| [Analysis](analysis/README.md) | Validation rules, failure handling, and observed constants |

For the Windows PE format, see the [Windows internals Space](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy).

This is a research reference. It records observed structures and validation behavior; it does not document a product workflow or a general-purpose unpacking procedure.
