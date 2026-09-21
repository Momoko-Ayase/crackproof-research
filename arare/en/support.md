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

Managed execution covers Framework 4.8 x86/x64, CoreCLR 10.0.12 x64, and Mono 6.13 x86 on applicable hosts. Pure-IL assemblies with only the COR20 `ILONLY` bit clear are accepted when they satisfy the restrictions below.

## Explicit refusals

- Native PE32 EXEs that require section-name or permission normalization for executable Senbei import recovery.
- Native inputs with code exports and `IMAGE_GUARD_XFG_ENABLED`.
- Exported data deliberately placed in an executable section.
- Modern managed zero-import layouts whose unused RVA page `[0x1000,0x2000)` is occupied.
- Writable executable sections when page encryption is effectively on.

Managed packing also refuses:

- Genuine C++/CLI mixed mode, native CLR entry points or fixups, ReadyToRun/AOT, and non-IL method implementations.
- Strong-named or delay-signed assemblies, multi-module assemblies, and linked or exported module content.
- Native exports, native exception/startup tables, TLS, load configuration tables, or delay imports.
- Sections whose `VirtualSize` exceeds `SizeOfRawData`, pre-existing pointer or Edit-and-Continue metadata tables, and implemented CLI vararg methods.
- Input types in the reserved `Arare.Managed` namespace.

These are input constraints, not differences between the listed CLR hosts. Disabling an environment check doesn't enable an unsupported assembly layout.

Managed preparation also limits metadata expansion to 524,288 added generic-padding TypeDefs. Signature parsing permits 128 type levels and 65,536 type elements per parsed return type. Inputs that exceed these work limits are rejected; the limits don't define a hard process-memory budget.

Profiles describe observed structural families, not commercial cloud versions. Remaining commercial-fidelity gaps include host-directory admission, unidentified E-series objects, loaded-module integrity cadence, a verified commercial default matrix, and Windows 10 execution.
