---
description: "Command-line protect, inspect, and verify: profiles, checks, pages, and publication."
---

# Usage

A normal build produces `target/release/arare.exe`. It needs no Senbei checkout. Managed packing requires the separately built managed tools. A WPF front-end that builds the same command lines is documented in [GUI](gui.md).

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

Protected modules run CrackProof-style environment checks before decryption. Each logs its observed stage code and ends the process silently on failure.

Native EXEs use the broad observed check set. Native DLLs enable `crc-loader`, `vm-backdoor`, `vm-registry`, and `host-process`. Managed modules enable `crc-loader` and `vm-registry`; managed DLLs also enable `host-process`. Both DLL kinds therefore require a compatible protected EXE by default.

`--check NAME=on|off` toggles individual checks. Repeat the flag to combine overrides.

| Name | Stage |
| --- | --- |
| `antidebug` | 410 |
| `crc-loader` | 510 |
| `debug-port` | 520 |
| `kernel-debugger` | 52F |
| `vm-backdoor` | 540 |
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

Defaults are not free of false positives by design. `parent-process` rejects launchers other than `cmd.exe`/`explorer.exe`. `vm-backdoor` refuses machines with a hypervisor present, including VBS/Hyper-V hosts. Disable them for those environments.

`host-process` accepts compatible native and managed Arare EXEs, including different packing seeds. Use `--check host-process=off` to load a protected DLL in an ordinary host. The optional stamp is a cooperative runtime compatibility check, not cryptographic authentication.

`os-version` (C00) uses Arare's floor of Windows 10 build 10240. One observed commercial sample used 14251.

`legacy-debugger`, `openark-device`, and `cheat-engine-device` are optional and off by default. Layout-family names alone do not establish a commercial build's option defaults.

## Page encryption

With `--page-encrypt=on` the loader re-encrypts every executable application page in place after reconstruction and sets it to `PAGE_NOACCESS`. The stub module's handler decrypts a page on first touch. The file carries only descriptor tables, never ciphertext. The default mirrors observed builds: on for host EXEs, off for DLLs.

`--scribble=on` XORs selected bytes of resident decrypted pages between faults. It requires page encryption and defaults to off.

`--errlog=on` reports the closing `AAA-BBB-CCC` code to `\\.\mailslot\ErrLog-Pec`. It defaults to off.

Inputs with writable executable sections require `--page-encrypt=off`. Effective default-on and explicit-on requests reject them before publishing or replacing either output.

## Debug logs

Create the build's 12-hex folder under `%TEMP%` to enable logging. Its creation time must be within 48 hours. The runtime does not create a missing gate.

A DLL inherits its protected EXE's gate and folder across packing seeds. A missing, stale, or invalid host gate suppresses the DLL log even when the DLL's own gate is fresh. Without a protected-host context, the DLL uses its own gate.

Host validation and logging are independent: `host-process=off` does not turn off inheritance. Names use `HHMMSSmmmE-...` for EXEs and `HHMMSSmmmD-...` for DLLs.

## Output

Protection parses and encodes the complete representation before publication. Output files are staged, flushed, then renamed. The destination directory must already exist. Canonical path or symlink aliases of the input are refused. Replacing a distinct hard-link output replaces that directory entry and preserves the input bytes.

A fixed seed reproduces output for the same input, options, and compiled loader. Changing the compiler, runtime sources, or metadata writer can change bytes.
