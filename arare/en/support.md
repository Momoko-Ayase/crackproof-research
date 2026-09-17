---
description: "Tested families, hosts, and explicit input refusals."
---

# Support

The target is Windows 10/11. Current execution evidence is Windows 11 build 26100, with source-built x86/WOW64 and x64 programs. A separate Windows 10 run has not been performed.

The optional kernel provider has a separate build and validation boundary. It is experimental, has no `protect` option, and is not a claim of commercial driver compatibility or verified kernel enforcement.

| Input | Embedded families | Companion families |
| --- | --- | --- |
| Native x86 EXE/DLL | PE32 | PE32 |
| Native x64 EXE/DLL | Classic/modern PE32+ | Classic/modern PE32+ |
| Native x64 DLL | Legacy DLL | Not applicable |
| IL-only x86/AnyCPU DLL | PE32 | PE32 |
| Recognized IL-only x86/AnyCPU C# EXE | PE32 | PE32 |
| IL-only x64 DLL | Legacy/classic/modern PE32+ | Classic/modern PE32+ |
| IL-only x64 EXE | Classic/modern PE32+ | Classic/modern PE32+ |
| Pure-IL x86/AnyCPU/x64 DLL with `ILONLY` clear | Same as the IL-only row for its architecture | Same as the IL-only row for its architecture |

Native IL2CPP PEs use the native rows. Standalone `global-metadata.dat` obfuscation is outside this implementation.

Managed execution covers Framework 4.8 x86/x64, CoreCLR 10.0.12 x64, and Mono 6.13 x86 on applicable hosts. Assemblies that are pure IL with only the COR20 `ILONLY` bit clear — the Unity Mono-era shape — are accepted. Genuine C++/CLI mixed mode, ReadyToRun/AOT, strong names, and multi-module content are refused.

## Explicit refusals

- Native PE32 EXEs that require section-name or permission normalization for executable Senbei import recovery.
- Native inputs with code exports and `IMAGE_GUARD_XFG_ENABLED`.
- Exported data deliberately placed in an executable section.
- Modern managed zero-import layouts whose unused RVA page `[0x1000,0x2000)` is occupied.
- Writable executable sections when page encryption is effectively on.

Profiles describe observed structural families, not commercial cloud versions. Remaining commercial-fidelity gaps include host-directory admission, unidentified E-series objects, loaded-module integrity cadence, a verified commercial default matrix, and Windows 10 execution.
