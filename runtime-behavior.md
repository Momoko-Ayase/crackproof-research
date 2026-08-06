---
description: "What a protected binary does when it runs: boot sequence, anti-analysis checks, kernel setup, and page decryption."
---

# Runtime behavior

A protected binary's first thread of execution belongs to Crackproof, not the program. The loader walks a fixed pipeline: environment checks, anti-analysis sweeps, kernel-driver and submodule setup, then the staged decryption from [The staged loader](staged-loader.md), then — optionally — re-encryption of what it just decrypted, and only then a jump to the original entry point (OEP). This page describes that pipeline as observed at runtime.

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
| `A09` | VM check via hardware registry strings |
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

A second channel sends an encrypted log to the mailslot `\\.\mailslot\ErrLog-Pec<number>`. Both channels share a 9-digit error format, `AAA-BBB-CCC`: the unpacker status code at failure, a sub-stage, and a third field.

{% hint style="info" %}
**Locating a stage in the binary.** Status codes are written through a helper that encodes them as the 16-bit value `(code << 4) | 1`. Breaking at the log write, then searching the binary for that word as bytes (for example `0xC01` → `11 C0`), lands directly on the stage that emitted it — the fastest known way to map the loader's code.
{% endhint %}

## Environment and anti-analysis checks

The checks run before (and partly interleaved with) decryption. Grouped by what they target:

**Debuggers.** A kernel-debugger check (`52F`), a SoftICE/Syser-era check (`BE0`), and timing-sensitive decoys embedded in the loader code (below). The VMware backdoor probe (`540`) doubles as an emulator check: the `in eax, dx` backdoor instruction faults on real hardware and in most emulators but returns a magic value under VMware.

**Virtual machines.** Registry string checks (`A09`) against three values — `HKLM\Hardware\Description\System\SystemBiosVersion`, `HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation\SystemProductName`, and `HKLM\Hardware\Description\System\BIOS\SystemProductName` — matched at their beginnings against: `Virtual`, `VMware`, `Bochs`, `VBOX`, `VRTUAL`, `Microsoft Hyper-V`, `Parallels`. CPU feature flags are sometimes checked at the same stage (requiring hardware virtualization to be exposed to the guest).

**System integrity.** OS minimum/compatible version checks (`C00`/`B00`), a boot-options check for `testsigning` or `disableintegritychecks` (`C01`, which blocks the usual unsigned-driver analysis setups), and a check that `C:\Windows\msc.log.log` does not exist (`BD0`).

**Process integrity.** An injected-DLL sweep (`A0F`), an injected-thread sweep that first kills (`A07`) and then aborts if any remain (`A01`), a parent-process policy (`A03`), and — for protected DLLs — a host-process check (`A11`) that looks for the protector's own markers in the host. The `A07` sweep is why in-process analysis helpers must either run before it or sleep past it.

**Anti-hooking.** At `A08`/`A04` the loader copies the *code* of ntdll/kernel32 from the pristine system DLLs on disk into memory and prefers that copy, defeating usermode inline hooks on those modules; `A04` aborts if the on-disk image is itself patched.

## Page-level encryption

The strongest runtime layer is optional and per-module. When enabled (`640` then `840`):

1. Executable sections are bulk-decrypted (status `640`).
2. They are then **re-encrypted page by page**, and every page is set to `PAGE_NOACCESS` (status `840`).
3. Execution that reaches a protected page faults; an exception handler decrypts the page on demand and resumes execution.

The exception handling is installed by **patching `ntdll!KiUserExceptionDispatcher`** to jump into the protector's handler, which chains back to normal SEH when it is done. The kernel delivers every usermode exception to this single entry point, so the handler runs ahead of all SEH registrations — and is invisible to tools that walk the SEH chain looking for hooks.

A consequence for memory analysis: a naive dump of a page-encrypted module captures only the pages touched since startup (the demand-decrypted working set); the rest is ciphertext or `PAGE_NOACCESS` filler. A complete image requires forcing every page to fault in first. Some builds additionally **scribble**: selected bytes of each decrypted page are XORed with random values once the page is resident, so a raw dump needs de-scribbling. The scribble is a per-build option and not always present — some page-encrypted modules dump cleanly once every page has been touched.

The page-fault handler does not live inside the protected module's image. It ships in a manually mapped support module (`HtdpStub2.dll` — see [Kernel drivers and submodules](kernel-components.md)), which is why handler signatures are absent when only the main module is dumped.

## The loader's own code: polymorphism and decoys

The loader defends its code as aggressively as its data. Techniques observed in the final stage (stage 5) and its bootstrap:

**Polymorphic emit.** The same algorithm appears as many permuted copies — one observed image carries 16 instances of one cipher prologue, differing only in cosmetic junk-jump placement. Disassemblers see 16 unrelated functions; the semantics are identical.

**Anti-disassembly.** Junk bytes after unconditional jumps, jumps into the middle of multi-byte instructions, and return-address arithmetic (for example `call $+5` followed by add/sub of two constants whose difference is the distance to the real continuation, the modified return address then being discarded). Linear and even recursive-descent disassembly desynchronize; one 12.9 KB stage-5 blob decompiles almost entirely to "control flows out of bounds".

**No-op decoy stubs.** The natural entry points are traps for the analyst's patience, not real code. One stub saves all 16 GPRs, performs the VMware backdoor probe, compares the result, and then executes `jne $+2` with a displacement of 0 — both branches reach the same instruction — restores every register, and returns. Its only side effect is the **timing** of the `in` instruction, consumed elsewhere. Another decoy hides its payload behind a trap flag: `pushfq; or [rsp], 0x100; popfq` raises `#DB`; under normal execution an SEH redirect skips the code after it, and only if a debugger (or naive emulator) swallows the exception and continues does the "hidden" path run — a path that goes nowhere useful.

**Self-modifying metadata.** Stage tables are zeroed after use: markers present in the pre-load image are overwritten by the time the module finishes initializing, so a post-boot dump is missing structures the static file contains.

## Self-loading from disk

The final stage does not do reflective in-memory loading. Its API string table contains `GetModuleFileNameW/A`, `CreateFileW`, `CreateFileMappingA`, `MapViewOfFile`, `UnmapViewOfFile`, `GetFileSize`, `GetFullPathNameW/A`, `CloseHandle`, `RtlGetVersion`, `SystemTimeToFileTime`, `Sleep` — file I/O and module-path APIs, with no allocation, protection, or loader APIs. The stage resolves its own on-disk path, maps the protected file as a memory view, and reads the encrypted payload from that view. (This is also why a static analysis can hand the same algorithm the raw file bytes and replay it offline.)

Runtime state is held in a context structure addressed through a reserved register: function pointers at fixed slots, a doubly indirect pointer to the image buffer, and a per-slot table built by an unrolled `lea`-and-store sequence. API addresses are read from the module's own OS-resolved import table — no PEB walk appears anywhere in the stage, so the module relies on the ordinary Windows loader having bound its imports, even though its stored `AddressOfEntryPoint` is junk and the OS never calls its real entry.

The same stage contains its own `.reloc` walker: relocations are applied by the loader (status `655`), not the OS, consistent with the `/FIXED` handling in [PE transformations](pe-transformations.md).
