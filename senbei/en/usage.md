---
description: "Command-line usage: file, package, and folder targets, flags, and exit codes."
---

# Usage

```text
senbei <file|folder> [--out DIR] [-v|--verbose] [-q|--quiet]... [--scan-all] [--strict-integrity] [--no-log] [--no-pause] [-V|--version] [-h|--help]
```

## Single file

Senbei writes the output below `<parent>/unpack/` with `.unpack` inserted before the extension. `--out DIR` changes both the output and the log directory.

```cmd
senbei app.exe
senbei app.exe --out C:\out
```

For `global-metadata.dat`, Senbei writes `global-metadata.unpack.dat` only when method tokens change. Unsupported metadata versions stay untouched and are reported as skipped.

## Android targets

Senbei restores protected `.so` files from their encrypted payload sections and writes them as `libil2cpp.unpack.so` or the corresponding input name. It treats APK, APKS, and XAPK files as containers: it reads their manifests first, follows nested APKs when necessary, and extracts only `.so` and exact `global-metadata.dat` entries.

If a restored library contains embedded metadata, Senbei writes the unwrapped blob beside it as `global-metadata.unpack.dat`. It restores identical loose and package entries once, preferring the loose file.

## Folder mode

Folder mode walks recursively, skips directories named `unpack`, and mirrors recognized outputs below `<root>/unpack/` or `--out DIR`. Windows candidates are `.exe`, `.dll`, and `global-metadata.dat`; Android candidates are `.so` and `global-metadata.dat`. A matching `.exe._` or `.dll._` payload is consumed by its stub and is excluded from the skipped count.

Managed DLL companions retain CLR metadata and related runtime tables in the original DLL. Both the DLL and its matching `._` file must be available; Senbei restores the declared CLR regions from the DLL while retaining method bodies decrypted from the companion. Missing or unreadable referenced regions are reported as errors.

`Companion missing?` means Senbei recognized a PE32+ loader entry record that explicitly declares the `._` suffix, but no companion was supplied. Put `<input>._` beside the input, keeping the complete filename (for example, `module.dll._`), or add both files in the browser. This check validates the PE structure, protection signature, and entry record; it doesn't prove that every part of the stub is intact. File size, hollow sections, and unpack failures alone don't trigger this hint. Damaged or unrecognized entry records keep the original unpack error.

If a supplied companion is too short to contain the 32-byte pairing header or its header differs from the recognized loader's, Senbei reports `Companion doesn't match`. Use both files from the same build; either file may be damaged. A companion that can't be read produces a file-read error. A matching header followed by a decryption failure keeps the original unpack error.

The summary has the form `12 unpacked · 3 skipped · 0 errors · 1 suspect · 2 metadata`; the package count is appended when packages were opened. Each file is isolated, so one failed target doesn't stop the folder run.

## Integrity check

Senbei checks PE outputs for valid headers, section ranges, entry-point mapping, readable import names, relocation requirements, and managed metadata signatures. It validates Android outputs during ELF restoration, including decoded container sizes, fixup bounds, and rebuilt dynamic tables.

A clean report isn't a proof of correctness, but a non-clean report is a reliable broken-output signal. Suspect PE files are still written and counted separately. `--strict-integrity` doesn't change that write; it only changes the process exit code.

## Flags

| Flag | Behavior |
| --- | --- |
| `--out DIR` | Write outputs and logs below `DIR`. |
| `-v`, `--verbose` | Print per-stage progress. |
| `-q`, `--quiet` | Hide progress and per-file lines; repeat to suppress all standard output. |
| `--no-log` | Don't write a run log. |
| `--scan-all` | Probe every selected target-name candidate, including files too small for the default scan to open. |
| `--strict-integrity` | Not in a released build yet. Exit non-zero when any output fails the static integrity check (a suspect) or a file errors. Off by default: a suspect is still written and the process exits `0` unless a file errors. Repeat `-q` is unchanged. |
| `--no-pause` | Disable the Explorer-friendly Windows exit prompt. |
| `-V`, `--version` | Print the version and exit. |
| `-h`, `--help` | Show usage. |

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | The requested restore completed without errors. A suspect output still exits `0` unless `--strict-integrity` is set. |
| `1` | A target failed, a scan probe was unreadable, or a single-file restore errored. With `--strict-integrity` (not released yet), any suspect output also exits `1`. Outputs are still written. |
| `2` | The command line was rejected. |
