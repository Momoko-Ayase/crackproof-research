---
description: "The three Htsysm kernel driver generations: shellcode execution, bounded EPROCESS edits, and ObRegisterCallbacks."
icon: gears
---

# Htsysm kernel components

CrackProof's optional kernel layer (`Htsysm`) has evolved across three distinct driver architectures:

{% tabs %}
{% tab title="Gen 1: HtsysmNT" %}
### Unauthenticated kernel shellcode execution

Generation 1 exposes an unauthenticated IOCTL that executes caller-supplied ring-0 shellcode. CrackProof's usermode `cm` helper uses that primitive to manually map two kernel-mode DLLs (`HtsyskNT.dll` at status `B21` and `HtpecmNT.dll` at status `BB0`) and invoke their `_FarEntry@0` exports for kernel memory access and process termination. Because any local usermode process can issue the same IOCTL, installing the driver grants arbitrary ring-0 code execution to the entire machine.
{% endtab %}

{% tab title="Gen 2: Htsysm7679" %}
### Bounded `EPROCESS` masked DWORD edits (`0xAA01`)

Generation 2 (`Htsysm7679`, device type `0xAA01`, IOCTLs `0xAA013880` / `0xAA013884` / `0xAA013888`) removes general shellcode execution and instead performs masked 32-bit clear, set, or read operations on `IoGetCurrentProcess() + offset` with unsigned `offset < 0x1000`.

* **Protected Process (`PP`) toggle:** at `C03`/`C04`, the loader sets the current process's `EPROCESS` Protected Process bitfields so usermode debuggers and injectors cannot open full-access handles. Because `PP` breaks certain Win32/NT calls (such as `NtCreateSection`), the usermode loader hooks those functions (logged under `C04`) to clear `PP`, call the original API, and set `PP` again.
* **BYOVD exposure:** caller validation relies only on a reversible per-PID cipher, so any local process that reproduces the PID transform can modify fields within its own `EPROCESS` (`offset < 0x1000`), or inject into a target before `C04` activates `PP`.
{% endtab %}

{% tab title="Gen 3: Htsysm767901 & Htsysm1B4001" %}
### `ObRegisterCallbacks` handle filtering (`0xAA02`)

Generation 3 (`Htsysm767901` and `Htsysm1B4001`, device type `0xAA02`, 12 IOCTLs `0xAA023800..0xAA02382C`) drops `EPROCESS` editing completely and registers an object-manager callback (`ObRegisterCallbacks`; altitude `88180.011104000001` on `Htsysm1B4001`, derived from `1B4001`) tracking up to 100 protected processes and a 12-entry telemetry ring.

* **Stripped access mask (`& 0xFFFFFFC5`, clearing `0x3A`):** removes `PROCESS_CREATE_THREAD` (`0x02`), `PROCESS_VM_OPERATION` (`0x08`), `PROCESS_VM_READ` (`0x10`), and `PROCESS_VM_WRITE` (`0x20`) from unapproved handle opens/duplications.
* **Exemption rules:** allows `KernelHandle`, self-access, up to 5 configured caller PIDs (`0xAA02380C`), up to 3 configured caller-parent PIDs (`0xAA023810`), and `csrss.exe`, `lsass.exe`, `conhost.exe`, or `svchost.exe` **only when executing from the configured system directory** (`0xAA023800`, plus an expected parent PID `0xAA023814` for `svchost.exe`).
* **Three-state handshake:** enrollment uses self-code and return-address hashing rather than a static PID cipher, and grants no kernel write primitive to usermode callers.
{% endtab %}
{% endtabs %}

## Version stamps (`0x7679` and `1B40`)

`0x00007679` in `Htsysm7679` / `Htsysm767901` matches the `0x00007679` configuration-cluster stamp in PE32 `EighthStage` and Stage 5 marker tables (see [PE32, DLL, and marker-less layouts](../loading-and-pe-repair/loading/layout-variants.md)). Newer Windows builds logging `Htsysm1B4001` at `C02`/`C03` share the `1B40` stamp seen in Android builds, use the Generation-3 `0xAA02` callback driver (with fewer usermode API hooks needed at `C04`), and frequently enable `E`-series device checks (`E55`, `E91`).

## Summary table

| Component | Layer | Role |
| --- | --- | --- |
| `HtpecIt.dll` (`it`) | Manually mapped usermode DLL | `Axx` anti-tamper, injection, VM, and host checks |
| `HtdpStub2.dll` (`dt`) | Manually mapped usermode DLL | Demand-decrypt page-fault handler and page tables |
| `HtsyskNT.dll` (`sk`) / `HtpecmNT.dll` (`pm`) | Gen-1 kernel DLLs | Kernel manual mapper (`B21`) and process monitor (`BB0`) |
| `HtsysmNT` | Kernel driver (Gen 1) | Unauthenticated ring-0 shellcode execution |
| `Htsysm7679` | Kernel driver (Gen 2, `0xAA01`) | Bounded (`offset < 0x1000`) masked DWORD edits on current `EPROCESS` |
| `Htsysm767901` / `Htsysm1B4001` | Kernel driver (Gen 3, `0xAA02`) | `ObRegisterCallbacks` handle-right stripping with path/PID exemptions |
