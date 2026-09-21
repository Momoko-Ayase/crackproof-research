---
description: "Command-line protect, inspect, and verify: profiles, checks, pages, and publication."
---

# Usage

A normal build produces `target/release/arare.exe`. It needs no Senbei checkout. Managed packing requires the separately built managed tools and the .NET 10 runtime. Place the three managed-tool files in `managed/` beside `arare.exe`, or set `ARARE_MANAGED_TOOLS` to their absolute directory; see [Development](development.md). A WPF front-end that builds the same command lines is documented in [GUI](gui.md).

```text
arare protect INPUT --output OUTPUT --profile PROFILE
    [--seed 64_HEX_DIGITS] [--no-compression]
    [--storage embedded|companion] [--check NAME=on|off]...
    [--page-encrypt on|off] [--scribble on|off] [--errlog on|off]
    [--force] [--json]

arare inspect INPUT [--json]

arare verify INPUT --profile PROFILE [--companion PATH] [--json]
```

| Profile | Input family |
| --- | --- |
| `pe32` | PE32 x86/native and applicable x86/AnyCPU managed images |
| `pe64-classic` | Classic EXE-style PE32+ x64 EXEs and DLLs |
| `pe64-modern` | Marker-less EXE-style PE32+ x64 EXEs and DLLs |
| `legacy-dll` | Dedicated older PE32+ x64 DLL family |

The selected family is validated against the input. It does not name a public commercial version. See [Support](support.md) for restrictions within each family.

Companion storage produces the named PE and its matching `<filename>._` file. Keep them together. Existing outputs require `--force`. Omitted seeds come from Windows' cryptographic random source and are printed on success. `--no-compression` stores application blocks raw; required format and generated loader stages retain their own representation.

`verify` checks the representation with the independent native decoder. It does not launch the program. Companion verification automatically tries `<INPUT>._` when the 32-byte pairing header matches. A missing companion is hinted when that automatic file is absent.

## Environment checks

Protected modules run configurable environment checks during startup. Most run before payload reconstruction; optional E55/E91 device checks run after page sealing. A check failure ends the process silently. Debug logs record its stage when logging is enabled. Most stage codes follow observed CrackProof behavior; `541` is Arare's own Hyper-V guest policy.

Default enabled checks are:

| Module | Checks |
| --- | --- |
| Native EXE | `antidebug`, `crc-loader`, `debug-port`, `os-version`, `boot-options`, `vm-registry`, `injected-dll`, `injected-thread`, `clean-code` |
| Native DLL | `crc-loader`, `vm-registry`, `host-process` |
| Managed EXE | `crc-loader`, `vm-registry` |
| Managed DLL | `crc-loader`, `vm-registry`, `host-process` |

All other checks default to off. Both DLL kinds therefore require a compatible protected EXE by default. `vm-backdoor`, `parent-process`, and `hyperv-guest` are opt-in for every module kind.

`--check NAME=on|off` toggles individual checks. Repeat the flag to combine overrides.

| Name | Stage |
| --- | --- |
| `antidebug` | 410 |
| `crc-loader` | 510 |
| `debug-port` | 520 |
| `kernel-debugger` | 52F |
| `vm-backdoor` | 540 |
| `hyperv-guest` | 541 (Arare-specific) |
| `parent-process` | A03 |
| `os-version` | C00 |
| `boot-options` | C01 |
| `msc-log` | BD0 |
| `os-compat` | B00 |
| `vm-registry` | A09 |
| `injected-dll` | A0F |
| `injected-thread` | A07/A01 |
| `host-process` | A11 |
| `host-stamp` | optional A11 runtime-context validation |
| `clean-code` | A08 |
| `disk-integrity` | A04 |
| `legacy-debugger` | BE0 |
| `openark-device` | E55 |
| `cheat-engine-device` | E91 |

`vm-backdoor` remains opt-in. `--check vm-backdoor=on` probes the VMware backdoor protocol and rejects a matching response. It allows Hyper-V/VBS; the generic CPUID hypervisor bit doesn't trigger rejection. Explicit `--check parent-process=on` still rejects launchers other than `cmd.exe` or `explorer.exe`.

**Strongly discouraged:** `hyperv-guest` is a separate check, off by default for every module kind. `--check hyperv-guest=on` rejects a reported Hyper-V-compatible guest using validated `Hv#1` CPUID partition privileges. It permits host/root partitions, including VBS, and unknown or incomplete classifications. Guest detection is heuristic: nested, masked, or spoofed environments can evade it. This is a compatibility restriction, not reliable protection.

`vm-registry` stays on by default. When the `Hv#1` interface identifies a Hyper-V-compatible environment, this check permits the generic `Virtual`, `VRTUAL`, and `Microsoft Hyper-V` registry markers. Explicit markers for other VM vendors still trigger rejection. The separate `hyperv-guest` opt-in controls rejection of Hyper-V-compatible guests.

Existing protected files keep the checks from the build that created them. To apply the revised checks and defaults, protect the original inputs again with the updated build. Saved explicit `on` overrides in the GUI or command scripts remain active; clear them or set them to `off` for any opt-in restrictions you don't want.

`host-process` accepts compatible native and managed Arare EXEs, including different packing seeds. Use `--check host-process=off` to load a protected DLL in an ordinary host. `host-stamp` adds validation only for DLLs with `host-process` enabled. The optional stamp is a cooperative runtime compatibility check, not cryptographic authentication.

Enabling `disk-integrity` replaces `clean-code`, even if both are requested. Both route loader calls through pristine system code; `disk-integrity` also validates the on-disk images against trusted system images.

`os-version` (C00) uses Arare's floor of Windows 10 build 10240. One observed commercial sample used 14251.

`legacy-debugger`, `openark-device`, and `cheat-engine-device` are optional and off by default. Layout-family names alone do not establish a commercial build's option defaults.

## Page encryption

With `--page-encrypt=on` the loader re-encrypts executable application pages in place after reconstruction and sets them to `PAGE_NOACCESS`. The stub module's handler decrypts a page on first touch. The page ciphertext is created at runtime; the file's payload still uses the selected format's encoding. The default is on for host EXEs and off for DLLs, matching the observed configurations.

`--scribble=on` XORs selected bytes of resident decrypted pages between faults. It requires page encryption and defaults to off.

`--errlog=on` sends a best-effort diagnostic report to `\\.\mailslot\ErrLog-Pec<suffix>`, where `<suffix>` is four hexadecimal digits derived from the logging identity. The report includes a timestamp, the closing `AAA-BBB-CCC` code, and the module path. Failure reports can also include loaded-module or OS details. This channel works independently of the debug-log folder and defaults to off; delivery requires a listener at the matching mailslot.

Inputs with writable executable sections require `--page-encrypt=off`. Effective default-on and explicit-on requests reject them before publishing or replacing either output.

## Debug logs

`protect --json` returns `log_folder`, the module's own 12-character uppercase hexadecimal logging identity. Create that folder under `%TEMP%` to enable its log. Its creation time must be within 48 hours. The runtime doesn't create a missing gate.

A DLL inherits its protected EXE's gate and folder across packing seeds. A missing, stale, or invalid host gate suppresses the DLL log even when the DLL's own gate is fresh. Without a protected-host context, the DLL uses its own gate. For a protected host, use the EXE's reported `log_folder`; the DLL's reported value identifies its fallback folder.

Host validation and logging are independent: `host-process=off` does not turn off inheritance. Names use `HHMMSSmmmE-...` for EXEs and `HHMMSSmmmD-...` for DLLs.

## Output

Protection parses and encodes the complete representation before publication. Output files are staged, flushed, then renamed. The destination directory must already exist. Canonical path or symlink aliases of the input are refused. Replacing a distinct hard-link output replaces that directory entry and preserves the input bytes.

A fixed seed reproduces output for the same input, options, and compiled loader. Changing the compiler, runtime sources, or metadata writer can change bytes.
