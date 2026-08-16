---
description: "The runtime boot sequence, status values, and diagnostic logging left by protected binaries."
---

# Startup sequence and status reporting

A protected binary's first thread of execution belongs to CrackProof, not the program. The loader walks a fixed pipeline: environment checks, anti-analysis sweeps, kernel-driver and submodule setup, then the staged decryption from [The staged loader](../loading/README.md), then — optionally — re-encryption of what it just decrypted, and only then a jump to the original entry point (OEP). This page describes that pipeline as observed at runtime.

## The boot sequence and status codes

The loader reports progress as 12-bit **status codes**, roughly one per stage. The list is not exhaustive — stages are configurable per build, so any given binary shows a subset:

| Code | Stage |
| --- | --- |
| `200` | Startup |
| `210` | Host architecture check |
| `52F` | Kernel-debugger check |
| `540` | VMware backdoor probe (and/or CPU feature flags) |
| `C00` | OS minimum-version check |
| `C01` | Boot-option check (`testsigning`, `disableintegritychecks`) |
| `C03` | Initialize the newer Htsysm driver |
| `C04` | Set the Protected Process flag; install hooks |
| `A0F` | Injected-DLL check |
| `A09` | VM check using hardware registry strings |
| `A08` | Copy clean ntdll/kernel32 code from disk to memory |
| `A04` | Same, aborting if the on-disk copy is patched |
| `A07` | Terminate injected threads |
| `A01` | Abort if injected threads are found |
| `A03` | Parent-process check (`cmd.exe` / `explorer.exe`) |
| `A11` | For DLLs: check the host process (a `peC` section, or imports from `KeRnEl32.dLl`) |
| `B00` | OS compatible-version check |
| `B21` | Load `HtsyskNT.dll` (old driver path) |
| `BD0` | Ensure `C:\Windows\msc.log.log` does not exist |
| `BE0` | SoftICE/Syser debugger check |
| `BB0` | Load `HtpecmNT.dll` (old driver path) |
| `5C0` | Load runtime DLLs (missing ones are logged) |
| `640` | Decrypt executable pages |
| `655` | Relocation |
| `840` | Install the exception-handler hook; re-encrypt executable pages |
| `280` | Jump to the OEP |

Observed sequences confirm features are per-module: in one title, the host EXE logs `640 … 840` (bulk decrypt, then page re-encryption), while a native plugin DLL in the same process goes from `610` (section decryption) straight to `655` — bulk-decrypted once, never page-encrypted.

## Debug logging

The loader's Achilles' heel: if a specific folder exists under `%temp%`, every protected module in the process writes a verbose debug log there as it unpacks. The folder name is 12 hexadecimal characters, differs per executable, and the easiest way to learn it is to break on or hook `CreateFileW`. Log lines carry the status codes above plus occasional free-form diagnostics (missing DLL names, hooked-function lists, addresses).

A second channel sends an encrypted log to the mailslot `\\.\mailslot\ErrLog-Pec<number>`. Both channels share a 9-digit error format, `AAA-BBB-CCC`: the recovery status code at failure, a sub-stage, and a third field.

{% hint style="info" %}
**Locating a stage in the binary.** Status codes are written through a helper that encodes them as the 16-bit value `(code << 4) | 1`. Breaking at the log write, then searching the binary for that word as bytes (for example `0xC01` → `11 C0`), lands directly on the stage that emitted it — the fastest known way to map the loader's code.
{% endhint %}

