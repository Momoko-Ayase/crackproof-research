---
description: "Embedded helper DLLs (HtpecIt, HtdpStub2, cm, dm, sk, pm) manually mapped via HtdpsCmnGetFileInfo."
icon: layer-group
---

# Manually mapped helper modules

CrackProof keeps major runtime subsystems out of the protected binary's own sections by embedding auxiliary DLLs inside the loader payload and mapping them through an internal loader (`HtdpsCmnGetFileInfo`) keyed by a two-letter module code.

## Submodule catalog

`HtdpsCmnGetFileInfo` manually maps the requested helper DLL into private executable memory (keeping it out of `PEB` loader lists walked by `InLoadOrderModuleList` and `CreateToolhelp32Snapshot`), resolves its entry point from its PE header, and can zero its `MZ` and `PE\0\0` signatures afterward:

| Two-letter code | Module name | Status range | Runtime role |
| --- | --- | --- | --- |
| `it` | `HtpecIt.dll` | `Axx` | Usermode anti-tamper, anti-injection, VM registry, and host-process checks |
| `dt` | `HtdpStub2.dll` | `8xx` / fault time | Demand-decrypt page-fault handler (`KiUserExceptionDispatcher` target) and per-page tables |
| `cm` | (usermode helper) | `Bxx` | Generation-1 `Htsysm` driver setup |
| `dm` | (usermode helper) | `Cxx` | Generation-2 and Generation-3 `Htsysm` driver setup and IOCTL handshake |
| `sk` | `HtsyskNT.dll` | `B21` | Generation-1 kernel DLL: kernel manual mapper and memory/I/O primitives |
| `pm` | `HtpecmNT.dll` | `BB0` | Generation-1 kernel DLL: process monitoring and termination |

Because `dt` (`HtdpStub2.dll`) owns both the page-decryption routine and the region/page descriptor arrays (see [Page protection and loader code](page-protection.md)), dumping only the main `.exe` or `.dll` module omits the page-fault handler altogether; locate `dt` in private executable VAD regions or follow the inline jump at the start of `ntdll!KiUserExceptionDispatcher`. Kernel-side counterparts are covered on [Htsysm kernel components](kernel-components.md).
