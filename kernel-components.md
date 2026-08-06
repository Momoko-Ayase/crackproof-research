---
description: "Crackproof's out-of-image components — the manually mapped helper DLLs loaded by two-letter module codes, and the three generations of the Htsysm kernel driver that provide protected-process status and handle restrictions."
---

# Kernel drivers and submodules

Not everything Crackproof runs lives inside the protected module. Two support ecosystems exist: **manually mapped usermode DLLs** (loaded by the loader, invisible to the Windows loader) and a **kernel driver line** called Htsysm (three generations with sharply different designs). This page covers both.

## Manually mapped submodules

The loader maps auxiliary DLLs into the process itself via an internal module loader, addressed through the function `HtdpsCmnGetFileInfo` with a two-letter module code. The call loads the DLL into memory and retrieves its entry point from its PE header. In memory these modules are deliberately harder to spot: their `MZ` and `PE` magic values can be zeroed out, though they are otherwise intact and straightforward to examine once located (the struct passed to the internal loader is the easiest anchor).

| Code | Module | Status group | Role |
| --- | --- | --- | --- |
| `it` | `HtpecIt.dll` | `Axx` | Anti-tamper, anti-injection, anti-VM checks |
| `dt` | `HtdpStub2.dll` | — | Additional loader code — including the demand-decrypt page-fault handler for [page-level encryption](runtime-behavior.md#page-level-encryption) |
| `cm` | (usermode init) | `Bxx` | Old Htsysm driver initialization |
| `dm` | (usermode init) | `Cxx` | New Htsysm driver initialization |
| `sk` | `HtsyskNT.dll` | `B21` | Old driver path: kernel manual-mapper, basic kernel I/O and memory functions |
| `pm` | `HtpecmNT.dll` | `BB0` | Old driver path: process monitoring/termination (kills analysis tools) |

The placement of the page-fault handler in `dt` explains a recurring observation: the protected module's own image contains no page-decryption code — the handler and its per-page key data live in a manually mapped module that naive module enumeration misses (it does not appear in the loader's module list; it shows up only as a private executable region).

## Htsysm generation 1: unauthenticated kernel shellcode (HtsysmNT)

The oldest driver's headline feature is an **unauthenticated IOCTL that lets any process execute kernel-mode shellcode**. Crackproof uses it to manually map kernel-mode DLLs (`HtsyskNT.dll`, then `HtpecmNT.dll`) and to call their `_FarEntry@0` export, which implements the rest of its kernel functionality — including, per the module notes, watching for and terminating analysis processes.

The security posture is as bad as it sounds: any process on the system can ask the driver to run arbitrary code in ring 0.

## Htsysm generation 2: EPROCESS editing (odd.sys / Htsysm7679)

The second generation is much more restricted in intent: it lets a process **write to its own `EPROCESS`**, allowing it to edit information about itself. Crackproof uses exactly one feature of this: setting the **Protected Process (PP) flag** so usermode tooling cannot open, read, or inject into the protected process (status `C03`/`C04`).

Two further details:

- Some APIs misbehave under PP (`NtCreateSection` among them), so the loader hooks those functions to temporarily drop the PP flag, call the original, and re-enable it. The hooked-function list appears in the debug log.
- The access "authentication" is a per-process-ID encryption scheme — but any program that correctly encrypts its process ID gets the same `EPROCESS` write primitive, which is equivalent to arbitrary kernel memory access. A second abuse path: inject a DLL into a process before it gains PP, then enjoy protected status for the injected code. Despite this, the driver has shipped with a valid WHQL signature, making it a practical bring-your-own-vulnerable-driver (BYOVD) candidate.

Undoing the PP flag requires kernel-level access (a kernel or hypervisor debugger, a PP-toggling driver, or hooking `DeviceIoControl` before the flag is set).

## Htsysm generation 3: handle restriction (io4.sys / Htsysm767901)

The newest generation abandons privilege-granting entirely. Instead it **denies unapproved processes handles with dangerous access rights** to protected processes: `PROCESS_CREATE_THREAD`, `PROCESS_VM_OPERATION`, `PROCESS_VM_READ`, and `PROCESS_VM_WRITE`. Approved processes are a fixed allowlist of system binaries (`svchost.exe`, `csrss.exe`, `lsass.exe`, `conhost.exe`).

This generation has a more thorough authentication check than its predecessors, grants protected processes no special powers of their own, and offers little of value to malware — the first design in the line that restricts itself to defense.

## The `0x7679` version stamp

The driver names encode a build stamp: `Htsysm7679` and `Htsysm767901` (= `7679` variant `01`). The same dword `0x00007679` appears inside protected files as the **configuration-cluster stamp** in the 32-bit loader's final stage (see [The staged loader](staged-loader.md)), and as half of an 8-byte tag inside stage-5 marker tables. It functions as a version identifier tying a protected build to its driver generation, and is a useful fingerprint when classifying unknown samples.

## Quick reference

| Component | Kind | Purpose |
| --- | --- | --- |
| `HtpecIt.dll` | Manual-mapped usermode DLL | Anti-tamper/injection/VM checks (`Axx` stages) |
| `HtdpStub2.dll` | Manual-mapped usermode DLL | Loader extension; page-fault demand-decrypt handler |
| `HtsyskNT.dll` | Kernel DLL (via gen-1 driver) | Kernel manual-mapper and I/O (`B21`) |
| `HtpecmNT.dll` | Kernel DLL (via gen-1 driver) | Process monitoring/termination (`BB0`) |
| HtsysmNT | Kernel driver, gen 1 | Unauthenticated kernel shellcode IOCTL |
| odd.sys / Htsysm7679 | Kernel driver, gen 2 | `EPROCESS` write; Protected Process flag |
| io4.sys / Htsysm767901 | Kernel driver, gen 3 | Handle access-right restriction |
