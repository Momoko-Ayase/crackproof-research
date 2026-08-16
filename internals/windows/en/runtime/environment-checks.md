---
description: "User-mode and kernel-assisted checks performed before control reaches the original program."
---

# Environment and anti-analysis checks

## Environment and anti-analysis checks

The checks run before (and partly interleaved with) decryption. Grouped by what they target:

**Debuggers.** A kernel-debugger check (`52F`), a SoftICE/Syser-era check (`BE0`), and timing-sensitive decoys embedded in the loader code (below). The VMware backdoor probe (`540`) doubles as an emulator check: the `in eax, dx` backdoor instruction faults on real hardware and in most emulators but returns a magic value under VMware.

**Virtual machines.** Registry string checks (`A09`) against three values — `HKLM\Hardware\Description\System\SystemBiosVersion`, `HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation\SystemProductName`, and `HKLM\Hardware\Description\System\BIOS\SystemProductName` — matched at their beginnings against: `Virtual`, `VMware`, `Bochs`, `VBOX`, `VRTUAL`, `Microsoft Hyper-V`, `Parallels`. CPU feature flags are sometimes checked at the same stage (requiring hardware virtualization to be exposed to the guest).

**System integrity.** OS minimum/compatible version checks (`C00`/`B00`), a boot-options check for `testsigning` or `disableintegritychecks` (`C01`, which blocks the usual unsigned-driver analysis setups), and a check that `C:\Windows\msc.log.log` does not exist (`BD0`).

**Process integrity.** An injected-DLL sweep (`A0F`), an injected-thread sweep that first kills (`A07`) and then aborts if any remain (`A01`), a parent-process policy (`A03`), and — for protected DLLs — a host-process check (`A11`) that looks for the protector's own markers in the host. The `A07` sweep is why in-process analysis helpers must either run before it or sleep past it.

**Anti-hooking.** At `A08`/`A04` the loader copies the *code* of ntdll/kernel32 from the pristine system DLLs on disk into memory and prefers that copy, defeating usermode inline hooks on those modules; `A04` aborts if the on-disk image is itself patched.

