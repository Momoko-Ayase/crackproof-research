---
description: "Debugger, VM, system-integrity, injected-module/thread, A11/A15 host, and anti-hooking checks at runtime."
icon: user-shield
---

# Environment and anti-analysis checks

CrackProof's startup checks span Phase 1 (before staging the payload), the `C`/`B`/`A` sequencer passes, and optional `E`-series post-seal checks:

{% tabs %}
{% tab title="Debuggers" %}
* **`410` (usermode anti-debug):** checks `IsDebuggerPresent` (live captures show no SEH-based sub-stages inside commercial `410`; trap-flag `#DB` SEH decoys live separately in Stage 5 loader code).
* **`520` & `52F`:** queries `NtQueryInformationProcess` debug classes (`520`) and kernel-debugger state (`52F`).
* **`BE0`:** checks legacy SoftICE / Syser driver device names.
* **Timing & `#DB` decoys:** Stage 5 interleaves `in eax, dx` timing reads and `pushfq; or [rsp], 0x100; popfq` single-step traps whose SEH handler skips dead decoy paths (see [Page protection and loader code](page-protection.md)).
{% endtab %}

{% tab title="Virtual machines" %}
* **`540` (VMware backdoor):** executes the `0x5658` I/O-port probe (`in eax, dx`), which raises `#GP` on bare metal and non-VMware hypervisors while returning magic data under VMware.
* **`A09` (hardware registry prefixes):** checks `HKLM\Hardware\Description\System\SystemBiosVersion`, `HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation\SystemProductName`, and `HKLM\Hardware\Description\System\BIOS\SystemProductName` for leading prefixes `Virtual`, `VMware`, `Bochs`, `VBOX`, `VRTUAL`, `Microsoft Hyper-V`, and `Parallels` (some builds also inspect CPU virtualization feature bits here).
{% endtab %}

{% tab title="System integrity" %}
* **`C00` & `B00`:** checks the real OS build (`0x01A00000 + build`) against a configured Windows 10+ floor (`C00`, defeating naive PEB version spoofing that lowers the reported build) and checks OS compatibility (`B00`).
* **`C01`:** rejects machines booted with `testsigning` or `disableintegritychecks` enabled.
* **`BD0`:** aborts if `C:\Windows\msc.log.log` is present.
* **`E55` & `E91`:** on `1B40`-family builds, probes symbolic device links associated with analysis drivers (such as OpenArk and Cheat Engine).
{% endtab %}

{% tab title="Process & host (A11 / A15)" %}
* **`A03`:** restricts parent process names (typically `explorer.exe` or `cmd.exe`).
* **`A0F`:** scans loaded modules (including `AppInit_DLLs`, `user32.dll`, `apphelp.dll`, and `ShimEng.dll`) and, on some host builds, rejects unexpected DLLs in the application directory.
* **`A07` & `A01`:** terminates unexpected foreign threads (`A07`) and aborts if any survive (`A01`).
* **`A11` (DLL host verification):** inspects the host EXE mapped in the current process and accepts either a section named `peC` or an import descriptor referencing exact-case `KeRnEl32.dLl` (Windows resolves the DLL case-insensitively while the mixed-case string marks a CrackProof host). A second `A11` variant checks an additional flag parameter.
* **`A15` (DLL sequencer marker):** carries no check body; emitted after `5D0` on protected DLL passes once `A09`/`A11` have succeeded. Host EXEs never log `A15` (logging `552`/`570` in that slot instead).
{% endtab %}

{% tab title="Anti-hooking" %}
* **`A08` & `A04`:** maps clean on-disk copies of `ntdll.dll` and `kernel32.dll` from `System32` and copies pristine `.text` bytes to bypass usermode inline hooks; `A04` additionally aborts if the on-disk system DLL itself has been modified.
{% endtab %}
{% endtabs %}
