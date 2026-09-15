---
description: "The helper-module roles embedded in the loader and mapped without the normal Windows loader."
---

# Manually mapped helper modules

Not everything CrackProof runs lives inside the protected module. The loader maps helper DLLs itself, so they stay invisible to the Windows loader. Kernel support is a separate driver line, Htsysm, in three generations with sharply different designs; see [Htsysm kernel components](kernel-components.md).

## Manually mapped submodules

The loader maps auxiliary DLLs into the process itself through an internal module loader, addressed through the function `HtdpsCmnGetFileInfo` with a two-letter module code. The call loads the DLL into memory and retrieves its entry point from its PE header. In memory these modules are deliberately harder to spot: their `MZ` and `PE` magic values can be zeroed out, though they are otherwise intact and straightforward to examine once located (the struct passed to the internal loader is the most convenient anchor).

| Code | Module | Status group | Role |
| --- | --- | --- | --- |
| `it` | `HtpecIt.dll` | `Axx` | Anti-tamper, anti-injection, anti-VM checks |
| `dt` | `HtdpStub2.dll` | — | Additional loader code, including the demand-decrypt page-fault handler for [page-level encryption](page-protection.md#page-level-encryption) |
| `cm` | (usermode init) | `Bxx` | Old Htsysm driver initialization |
| `dm` | (usermode init) | `Cxx` | New Htsysm driver initialization |
| `sk` | `HtsyskNT.dll` | `B21` | Old driver path: kernel manual-mapper, basic kernel I/O and memory functions |
| `pm` | `HtpecmNT.dll` | `BB0` | Old driver path: process monitoring/termination (kills analysis tools) |

The placement of the page-fault handler in `dt` explains a recurring observation: the protected module's own image contains no page-decryption code. The handler and its per-page key data live in a manually mapped module that naive module enumeration misses (it doesn't appear in the loader's module list; it shows up only as a private executable region).
