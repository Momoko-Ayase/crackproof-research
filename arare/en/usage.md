---
description: "Command-line protect, inspect, and verify: profiles, environment checks, page encryption, and debug logs."
icon: terminal
---

# Usage

Building `arare-cli` produces `target/release/arare.exe` with no Senbei checkout required. Managed packing additionally needs the .NET 10 runtime and the three managed-tool files (`Arare.ManagedHost.dll`, `Arare.ManagedHost.runtimeconfig.json`, `Arare.Bootstrap.dll`) placed in `managed/` beside `arare.exe` or pointed to by `ARARE_MANAGED_TOOLS` (see [Development](development.md)). Batch GUI usage is covered in [GUI](gui.md).

```text
arare protect INPUT -o|--output OUTPUT --profile PROFILE
    [--seed 64_HEX_DIGITS] [--no-compression]
    [--storage embedded|companion] [--check NAME=on|off]...
    [--page-encrypt on|off] [--scribble on|off]
    [--errlog on|off] [--antidebug-av on|off]
    [--force] [--json]

arare inspect INPUT [--json]

arare verify INPUT --profile PROFILE [--companion PATH] [--json]
```

## Profiles and storage

| Profile | Target layout family |
| --- | --- |
| `pe32` | PE32 x86 native images and supported x86/AnyCPU managed assemblies |
| `pe64-classic` | Classic marker-based EXE-style PE32+ x64 EXEs and DLLs |
| `pe64-modern` | Marker-less EXE-style PE32+ x64 EXEs and DLLs |
| `legacy-dll` | Dedicated older PE32+ x64 DLL layout (embedded storage only) |

Profile names identify structural layout families rather than commercial product versions; see [Support](support.md) for input constraints.

* **Companion storage (`--storage companion`):** writes both `OUTPUT` (the 4 KiB header/overlay stub) and `<OUTPUT>._` (the encrypted payload, paired by the 32-byte header at `0x1000..0x1020`). Keep both files in the same folder.
* **Seeds and compression:** omitting `--seed` draws 32 random bytes from Windows CSPRNG and prints the hex seed. `--no-compression` stores application section blocks uncompressed while keeping loader stage encodings intact.
* **Static verification (`verify`):** decodes the protected file with Arare's independent native decoder without executing the target. When `--companion` is omitted, `verify` automatically pairs `<INPUT>._` if its 32-byte header matches.

## Environment checks and failure response

Protected modules run configurable checks in three startup phases (Phase 1 before staging the file, Phase 2 after staging, and Phase 3 after page sealing). Repeat `--check NAME=on|off` to override defaults:

| Module kind | Default enabled checks |
| --- | --- |
| Native EXE | `antidebug`, `crc-loader`, `debug-port`, `os-version`, `boot-options`, `vm-registry`, `injected-dll`, `injected-thread`, `clean-code` |
| Native DLL | `crc-loader`, `vm-registry`, `host-process` |
| Managed EXE | `crc-loader`, `vm-registry` |
| Managed DLL | `crc-loader`, `vm-registry`, `host-process` |

Because `host-process` defaults to `on` for both DLL kinds, loading a protected DLL inside an unprotected host process requires `--check host-process=off`. `vm-backdoor`, `parent-process`, and `hyperv-guest` default to `off` for all module kinds.

| CLI check name | Stage code | Behavior |
| --- | --- | --- |
| `antidebug` | `410` | 7 sub-stages: `IsDebuggerPresent`, `PEB.BeingDebugged`, `PEB.NtGlobalFlag & 0x70`, hardware debug registers `DR0`..`DR3` / `DR7 & 0xFF` (`GetThreadContext`), and `NtQueryInformationProcess` (`ProcessDebugPort`, `ProcessDebugFlags == 0`, `ProcessDebugObjectHandle`) |
| `crc-loader` | `510` | Loader code CRC-32 self-check |
| `debug-port` | `520` | Kernel debug-port query |
| `kernel-debugger` | `52F` | `KdDebuggerEnabled` / system kernel-debugger check |
| `vm-backdoor` | `540` | VMware `0x5658` I/O port probe (ignores generic CPUID hypervisor bit; allows Hyper-V/VBS) |
| `hyperv-guest` | `541` | Arare-specific Hyper-V guest partition privilege check (`Hv#1` CPUID) |
| `parent-process` | `A03` | Rejects parent processes other than `explorer.exe` or `cmd.exe` |
| `os-version` | `C00` | Requires Windows 10 build `10240` or newer |
| `boot-options` | `C01` | Rejects test-signing / debug boot flags |
| `msc-log` | `BD0` | Rejects presence of `C:\Windows\msc.log.log` |
| `os-compat` | `B00` | OS compatibility gate |
| `vm-registry` | `A09` | System hardware/BIOS VM registry markers (allows generic `Virtual` / `VRTUAL` / `Microsoft Hyper-V` when `Hv#1` identifies Hyper-V/VBS) |
| `injected-dll` | `A0F` | Scans loaded modules before OEP |
| `injected-thread` | `A07` / `A01` | Detects unexpected foreign threads |
| `host-process` | `A11` | Requires a compatible Arare EXE host (`.arldr` or `.armclr` marker) |
| `host-stamp` | `A11` | Optional cooperative runtime-context stamp check when `host-process=on` |
| `clean-code` | `A08` | Routes loader calls through clean system DLL bytes |
| `disk-integrity` | `A04` | Replaces `clean-code` even if both are requested; also compares mapped system DLLs against on-disk system images |
| `legacy-debugger` | `BE0` | Legacy debugger device probe |
| `openark-device` | `E55` | Post-seal OpenArk driver device check |
| `cheat-engine-device` | `E91` | Post-seal Cheat Engine driver device check |

{% hint style="warning" %}
**Avoid enabling `hyperv-guest` unless specifically needed.** `--check hyperv-guest=on` rejects guest VMs identified through `Hv#1` CPUID partition privileges while permitting root/host VBS partitions. Hypervisor CPUID leaves can be masked or spoofed, so treat `hyperv-guest` as an environment restriction rather than tamper resistance.
{% endhint %}

**Failure response (`--antidebug-av`):** `--antidebug-av` defaults to `on` for EXEs and `off` for DLLs (logged as `-AV=ON` / `-AV=OFF` on native modules). When a check fails on a native module with `--antidebug-av=on`, the runtime closes the log, calls `RaiseException(0xC0000005)` (`EXCEPTION_ACCESS_VIOLATION`), and writes to null before calling `TerminateProcess(0xE0A00000 | substage)` so an attached debugger breaks immediately. Native modules with `--antidebug-av=off` and managed modules call `TerminateProcess` directly.

## Page encryption

`--page-encrypt` defaults to `on` for EXEs and `off` for DLLs. After section reconstruction, the runtime re-encrypts executable application pages in place, marks them `PAGE_NOACCESS`, and hooks `ntdll!KiUserExceptionDispatcher` to decrypt pages on first execution fault. Inputs with writable executable (`RWX`) sections or sub-`0x1000` section alignment are rejected when page encryption is enabled.

`--scribble=on` (default `off`, requires `--page-encrypt=on`) masks selected bytes of already-decrypted resident pages between faults.

## Debug logs and `ErrLog-Pec`

`protect --json` (and standard console output) reports the module's 12-hex-character `log_folder`. If `%TEMP%\<log_folder>` exists and is less than 48 hours old, the module writes runtime status logs (`HHMMSSmmmE-...` for EXEs, `HHMMSSmmmD-...` for DLLs) ending with an `AAA-BBB-CCC` closing summary.

{% hint style="info" %}
**DLL log-gate inheritance.** When a protected DLL loads inside a protected Arare EXE, the EXE's logging context always governs the DLL, even across different seeds and even when `host-process=off` is set. If the EXE's `%TEMP%` folder is missing or older than 48 hours, the DLL stays silent regardless of its own fallback `log_folder`.
{% endhint %}

`--errlog=on` (default `off`) sends a closing diagnostic packet to `\\.\mailslot\ErrLog-Pec<suffix>` (where `<suffix>` is four hex digits from `((key + 1) * 0x3039) % 0x8003`), carrying a timestamp, the `AAA-BBB-CCC` code, and module/OS details independently of the `%TEMP%` folder gate.

## Output writes and JSON reports

Outputs are encoded completely in memory, written to a staging file, flushed, and atomically renamed (`--force` is required to overwrite existing files). Symlink or canonical-path aliases of the input file are refused; replacing a separate hard-link entry preserves the original input bytes.

<details>
<summary>JSON output fields (protect, inspect, verify)</summary>

* **`protect --json`:** `output`, `profile`, `storage`, `architecture`, `module`, `input_size`, `output_size`, `seed`, `normalizations`, `log_folder`, `companion`, `companion_size`.
* **`inspect --json`:** `architecture`, `module`, `entry_point`, `image_base`, `image_size`, `file_size`, `sections` (`name`, `rva`, `virtual_size`, `raw_offset`, `raw_size`, `characteristics`).
* **`verify --json`:** `valid`, `profile`, `companion`, `image_size`, `recovered_file_size`, `entry_point`.
</details>
