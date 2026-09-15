---
description: "The observed Htsysm generations, their kernel responsibilities, and their version stamp."
---

# Htsysm kernel components

## Htsysm generation 1: unauthenticated kernel shellcode (HtsysmNT)

The oldest driver's headline feature is an **unauthenticated IOCTL that lets any process execute kernel-mode shellcode**. CrackProof uses it to manually map kernel-mode DLLs (`HtsyskNT.dll`, then `HtpecmNT.dll`) and to call their `_FarEntry@0` export, which implements the rest of its kernel functionality, including, per the module notes, watching for and terminating analysis processes.

The security posture is as bad as it sounds: any process on the system can ask the driver to run arbitrary code in ring 0.

## Htsysm generation 2: EPROCESS editing (Htsysm7679)

The second generation is much more restricted in intent: it lets a process **write to its own `EPROCESS`**, allowing it to edit information about itself. CrackProof uses exactly one feature of this: setting the **Protected Process (PP) flag** so usermode tooling can't open, read, or inject into the protected process (status `C03`/`C04`).

Two further details:

- Some APIs misbehave under PP (`NtCreateSection` among them), so the loader hooks those functions to temporarily drop the PP flag, call the original, and re-enable it. The hooked-function list appears in the debug log.
- The access "authentication" is a per-process-ID encryption scheme, but any program that correctly encrypts its process ID gets the same `EPROCESS` write primitive, which is equivalent to arbitrary kernel memory access. A second abuse path: inject a DLL into a process before it gains PP, then enjoy protected status for the injected code. Despite this, the driver has shipped with a valid WHQL signature, making it a practical bring-your-own-vulnerable-driver (BYOVD) candidate.

Undoing the PP flag requires kernel-level access (a kernel or hypervisor debugger, a PP-toggling driver, or hooking `DeviceIoControl` before the flag is set).

## Htsysm generation 3: handle restriction (Htsysm767901)

The newest generation abandons privilege-granting entirely. Instead it **denies unapproved processes handles with dangerous access rights** to protected processes: `PROCESS_CREATE_THREAD`, `PROCESS_VM_OPERATION`, `PROCESS_VM_READ`, and `PROCESS_VM_WRITE`. Approved processes are a fixed allowlist of system binaries (`svchost.exe`, `csrss.exe`, `lsass.exe`, `conhost.exe`).

This generation has a more thorough authentication check than its predecessors, grants protected processes no special powers of their own, and offers little of value to malware. It is the first design in the line that restricts itself to defense.

## The `0x7679` version stamp

The driver names encode a build stamp: `Htsysm7679` and `Htsysm767901` (= `7679` variant `01`). The same dword `0x00007679` appears inside protected files as the **configuration-cluster stamp** in the 32-bit loader's final stage (see [PE32, DLL, and marker-less layouts](../loading-and-pe-repair/loading/layout-variants.md)), and as half of an 8-byte tag inside stage-5 marker tables. It functions as a version identifier tying a protected build to its driver generation, and is a useful fingerprint when classifying unknown samples.

## The `Htsysm1B4001` device name

Some newer builds log the device name `Htsysm1B4001` at `C02`/`C03` instead of `Htsysm7679` or `Htsysm767901`. The `1B40` stamp also appears in the Android native-library family. This is another observed service and device name, not a fourth generation with its own documented privilege model. One observed log of this name listed fewer hooks at `C04` and continued into the `E`-series stages described in [Startup sequence and status reporting](startup-status.md).

## Quick reference

| Component | Kind | Purpose |
| --- | --- | --- |
| `HtpecIt.dll` | Manual-mapped usermode DLL | Anti-tamper/injection/VM checks (`Axx` stages) |
| `HtdpStub2.dll` | Manual-mapped usermode DLL | Loader extension; page-fault demand-decrypt handler |
| `HtsyskNT.dll` | Kernel DLL (loaded by the gen-1 driver) | Kernel manual-mapper and I/O (`B21`) |
| `HtpecmNT.dll` | Kernel DLL (loaded by the gen-1 driver) | Process monitoring/termination (`BB0`) |
| HtsysmNT | Kernel driver, gen 1 | Unauthenticated kernel shellcode IOCTL |
| Htsysm7679 | Kernel driver, gen 2 | `EPROCESS` write; Protected Process flag |
| Htsysm767901 | Kernel driver, gen 3 | Handle access-right restriction |
| Htsysm1B4001 | Device/service name | Observed on `1B40`-family Windows builds |
