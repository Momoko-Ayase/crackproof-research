---
description: "Supported PE and CLR input matrix, pack-time refusals, structural bounds, and runtime loading rules."
icon: circle-check
---

# Support

Arare targets Windows 10 and Windows 11, with execution verified on Windows 11 build 26100 across source-built x86/WOW64 and x64 native and managed programs (a separate Windows 10 test pass has not been run). Managed execution is verified on .NET Framework 4.8 (x86/x64), CoreCLR 10.0.12 (x64), and Mono 6.13 (x86).

## Supported input matrix

| Input kind | Embedded profiles | Companion (`._`) profiles |
| --- | --- | --- |
| Native x86 EXE or DLL | `pe32` | `pe32` |
| Native x64 EXE or DLL | `pe64-classic`, `pe64-modern` | `pe64-classic` (nonzero entry required on DLLs), `pe64-modern` |
| Native x64 DLL (dedicated layout) | `legacy-dll` | Not supported |
| IL-only x86 or AnyCPU DLL | `pe32` | `pe32` |
| Recognized IL-only x86 or AnyCPU C# EXE | `pe32` | `pe32` |
| IL-only x64 DLL | `legacy-dll`, `pe64-classic`, `pe64-modern` | `pe64-classic`, `pe64-modern` |
| IL-only x64 EXE | `pe64-classic`, `pe64-modern` | `pe64-classic`, `pe64-modern` |
| Pure-IL DLL with `COR20` `ILONLY` clear | Same as IL-only DLL for its bitness | Same as IL-only DLL for its bitness |

Native IL2CPP binaries (`GameAssembly.dll` and host EXEs) pack as ordinary native PEs; standalone `global-metadata.dat` obfuscation is outside Arare's scope.

## Pack-time refusals

`arare protect` rejects inputs with any of the following:

### Native and shared PE constraints

* **Zero-entry classic companion DLLs:** `pe64-classic` companion DLLs with a zero `AddressOfEntryPoint` (use embedded storage or `pe64-modern` for entryless DLLs).
* **Companion TLS overlap:** x64 companion inputs whose TLS entry range overlaps loader-preserved physical data.
* **Page-encryption alignment and permissions:** writable executable (`RWX`) sections, `SectionAlignment < 0x1000`, or executable sections whose `VirtualAddress` is not `0x1000`-aligned when page encryption is active.
* **Bound-only imports:** native import descriptors with `OriginalFirstThunk == 0` and no in-image hint/name RVA or VA.
* **PE32 EXE import normalization:** native PE32 EXEs that would require section-name or permission rewriting for static unpacker import recovery.
* **XFG code exports:** native modules combining code exports with `IMAGE_GUARD_XFG_ENABLED`.
* **Image and header ceilings:** total image size (including added Arare sections) above `1 GiB`, section count above `96`, or section headers exceeding `0x1000` bytes (`pe64-*` / `legacy-dll`) or `0x400` bytes (`pe32`).

### Managed assembly constraints

* Genuine C++/CLI mixed-mode code, native CLR entry points or vtable fixups, ReadyToRun/AOT images, or non-IL method bodies.
* Strong-named or delay-signed assemblies, multi-module assemblies, linked/exported module tables, embedded Portable PDBs, or CLI metadata tables `>= 45` (such as `/debug:embedded`).
* x86 managed EXEs with `ILONLY` clear, PE32+ managed inputs with `32BITREQUIRED` or `32BITPREFERRED` set, `pe64-modern` zero-import assemblies whose RVA page `[0x1000, 0x2000)` is occupied, or `pe64-modern` managed inputs with a nonzero import directory whose first descriptor is empty.
* Native exports, native exception/unwind or TLS directories, load-config tables, delay imports, sections with `VirtualSize > SizeOfRawData`, Edit-and-Continue/pointer metadata tables, CLI `vararg` methods, or types inside the reserved `Arare.Managed` namespace.
* Metadata expansion above `524,288` added generic-padding `TypeDef` rows, or signature return types exceeding `128` nesting levels or `65,536` type elements.

## Layout and runtime loading notes

* **Data exports inside executable sections:** PE export tables do not tag entries as code vs data, so non-forwarder exports pointing into an executable section are wrapped with a code-export guard thunk rather than rejected at pack time. Keep exported data symbols in non-executable data sections.
* **Byte-array vs disk loads:** companion-packed managed assemblies require on-disk files and reject `Assembly.Load(byte[])`. Pure-IL DLLs with `ILONLY` clear follow standard CLR mixed-mode loading rules (on-disk load in a matching-bitness process on .NET Framework/CoreCLR; Mono loads both disk and byte-array forms).
