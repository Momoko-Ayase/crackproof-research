---
description: "The runtime boot sequence, status values, and diagnostic logging left by protected binaries."
---

# Startup sequence and status reporting

A protected binary's first thread of execution belongs to CrackProof, not the program. The loader walks a fixed pipeline: environment checks, anti-analysis sweeps, kernel-driver and submodule setup, then the staged decryption from [Loading and section recovery](../loading-and-pe-repair/loading/README.md), then (optionally) re-encryption of what it just decrypted, and only then a jump to the original entry point (OEP). This page describes that pipeline as observed at runtime.

## The boot sequence and status codes

The loader reports progress as 12-bit **status codes**, roughly one per stage. The list isn't exhaustive. Stages are configurable per build, so any given binary shows a subset:

| Code | Stage |
| --- | --- |
| `200` | Startup |
| `210` | Host architecture check |
| `410` | Usermode anti-debug start |
| `510` | CRC-32 of a loader memory region |
| `520` | `NtQueryInformationProcess` check |
| `52F` | Kernel-debugger check |
| `540` | VMware backdoor probe (and/or CPU feature flags) |
| `560` | Code-section decrypt setup |
| `561` | Select a support module (absent or unused on some newer builds) |
| `C00` | OS minimum-version check |
| `C01` | Boot-option check (`testsigning`, `disableintegritychecks`) |
| `C02` | Install the Htsysm driver service. The log names the device (`Htsysm7679`, `Htsysm767901`, or `Htsysm1B4001`) and the on-disk driver file under `C:\Windows\System32`. That filename is a per-deployment artifact, not a format constant. |
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
| `A15` | For DLLs: host-trust marker logged after `5D0`; carries no check of its own and only appears once the earlier check chain has passed |
| `B00` | OS compatible-version check |
| `B21` | Load `HtsyskNT.dll` (old driver path) |
| `BD0` | Ensure `C:\Windows\msc.log.log` doesn't exist |
| `BE0` | SoftICE/Syser debugger check |
| `BB0` | Load `HtpecmNT.dll` (old driver path) |
| `5D0` `552` `570` `590` `5B0` `5B1` `598` `5A0` `5E1` `5E2` | Decrypt prelude stages |
| `A06` | Late API hooks, when the stage is logged |
| `5C0` | Load runtime DLLs (missing ones are logged) |
| `610` | Decrypt the PE header |
| `640` | Decrypt executable pages |
| `655` | Relocation |
| `6E1` | Tail work; some builds re-encrypt part of the executable range |
| `800` `810` `820` | Page-encrypt setup |
| `840` | Install the exception-handler hook; re-encrypt executable pages |
| `E20` `E40` `E52`–`E59` | Later integrity stages on some `1B40`-family builds |
| `E55` `E91` | Device-name checks for analysis-tool drivers |
| `660` | Stage after page-encrypt setup, before the OEP jump |
| `280` | Jump to the OEP |

Observed sequences confirm features are per-module: in one title, the host EXE logs `640 … 840` (bulk decrypt, then page re-encryption), while a native plugin DLL in the same process goes from `610` (section decryption) straight to `655`, bulk-decrypted once, never page-encrypted.

The `A`-series checks are not hard-wired into the stage walker. A single sequencer function drives them, and the walker calls it several times with different modes; each call runs only the subset of checks that the build's option flags select. A protected DLL is driven in its own mode. That is why a DLL log shows `A09` and `A11` before `5D0` and `A15` after it, while the host log for the same title shows `A09` `A0F` `A08` `A07` before `5D0` and `552` `570` after it.

The `C00` line logs two dwords. Each is `0x01A0` plus a Windows build number: the first is the host build, the second is the minimum accepted build. Observed minima correspond to Windows 10.

One observed `Htsysm1B4001` log listed fewer hooks at `C04` and continued into later `E`-series stages, including the device-name checks at `E55` and `E91`.

## Debug logging

The loader writes a verbose debug log for every protected module when a specific folder exists under `%temp%`. The folder name is 12 hexadecimal characters and differs per executable. The most direct way to learn the name is to break on or hook `CreateFileW`. The folder's creation time must be within about two days; an older folder is left in place, and that run writes no log.

Log lines carry the status codes listed in [The boot sequence and status codes](#the-boot-sequence-and-status-codes) plus occasional free-form diagnostics (missing DLL names, hooked-function lists, addresses).

A second channel sends an encrypted log to the mailslot `\\.\mailslot\ErrLog-Pec<number>`. Both channels share a 9-digit error format, `AAA-BBB-CCC`: the recovery status code at failure, a sub-stage, and a third field. Observed values include `046-019-01F` (kernel callbacks disabled), `048-012-002` (Hyper-V), and `601-000-008` (an analysis-tool driver).

{% hint style="info" %}
**Locating a stage in the binary.** Status codes are written through a helper that encodes them as the 16-bit value `(code << 4) | 1`. Breaking at the log write, then searching the binary for that word as bytes (for example `0xC01` → `11 C0`), identifies the stage that emitted it. That search is the fastest known way to map the loader's code.
{% endhint %}
