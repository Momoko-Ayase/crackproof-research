---
description: "Command-line usage: file, package, and folder targets, flags, and exit codes."
---

# Usage

```text
senbei [unpack] <file|folder> [options]
senbei inspect <file|folder> [--json] [options]
```

## Single file

Senbei writes the output below `<parent>/unpack/` with `.unpack` inserted before the extension. `--out DIR` changes both the output and the log directory.

```cmd
senbei app.exe
senbei app.exe --out C:\out
```

For `global-metadata.dat`, Senbei writes `global-metadata.unpack.dat` only when method fields change. Unsupported versions stay untouched. Folder runs report them as skipped; a direct-file restore reports an error.

## Inspection and JSON reports

The following commands are development features and aren't in a released build yet. The original `senbei PATH` form still restores files; `senbei unpack PATH` is an alias.

```cmd
senbei inspect module.dll
senbei inspect module.dll --json
senbei inspect module.dll --strict-integrity --json
senbei unpack module.dll --dry-run --json
senbei unpack module.dll --json --strict-integrity --no-pause
```

`inspect` is the research-oriented command. It reports source hashes, parsed format structures, decoded protection headers, candidate reasoning, discovered stage parameters, and structural checks. It runs the static recovery pipeline where needed to obtain that evidence, then discards recovered images instead of writing normal outputs or logs. It never executes the target. Ordinary file scanning still uses lightweight detection; inspection deliberately prioritizes detail over minimum processing time.

For Windows inputs, the report distinguishes the physical source, a companion-spliced analysis view when used, and the recovered image. It shows section ranges and permissions, data-directory mappings, unsectioned file regions, payload declarations, and actual discovery events with file-offset or working-image-RVA provenance. Header flags are declarations, not runtime guarantees. Probe limits and unavailable prerequisites are reported explicitly; a rejected candidate remains visible even when a later route succeeds.

Recognition doesn't establish that recovery succeeds. A metadata signature identifies IL2CPP data, not protection; a known header version doesn't validate its table layout. The research report preserves recovery failures as findings rather than replacing them with an unexplained unrecognized verdict. A successful inspection exit means the input was examined, not that recovery succeeded. Unreadable inputs and infrastructure failures still fail the command; `--strict-integrity` additionally checks any actual recovered-image verdict.

`--dry-run` checks the normal restoration and validation paths without retaining outputs or logs; it doesn't request the richer research trace. Senbei removes any temporary workspace when the run ends. `--dry-run` can't be combined with `--out`. Inspection also rejects `--out` and `--dry-run`, because discarding outputs is already part of inspection. `inspect --strict-integrity` can fail the command when an image actually recovered for inspection has a suspect integrity result.

`--json` writes a versioned machine-readable report to standard output instead of the banner, progress, and human-readable summary. An explicit JSON request still emits the report with `-q`; it disables run logs and the exit prompt. It records available profiles, actual stage outcomes, candidate attempts, diagnostics, and pairing provenance. Unattempted stages aren't marked successful. Static checks don't establish runtime loadability or complete analysis-tool coverage. Reports can contain local paths and content hashes; review them before sharing.

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

A clean report isn't a proof of correctness. Reports distinguish errors from warnings: a warning needs investigation, but doesn't necessarily mean that the loader rejects the file. New structural diagnostics don't change the existing DLL layout-selection gates. Suspect PE files are still written and counted separately. `--strict-integrity` doesn't change that write; it only changes the process exit code.

## Browser reports and input limits

The development browser build shows header-only profile information before recovery and the actual recovery and integrity results afterward. **Export JSON** downloads the report locally, including failures and blocked inputs. Metadata transformation runs in a disposable worker too; its report doesn't claim an independent PE/ELF integrity check.

**Input limit per module (MiB)** defaults to `256` and accepts values from `8` to `4096`. The browser budgets a base module and its matching `._` companion together before reading their full contents; staging reads only a small header slice. This isn't a peak-memory limit. Inputs, output images, and scratch buffers can coexist, and completed outputs remain available for download. For several large files, process them separately and clear completed rows. Raising the input limit doesn't guarantee that a file fits the browser's memory.

Android ELF and package recovery still require the native CLI. Browser inputs and reports aren't uploaded.

## Flags

| Flag | Behavior |
| --- | --- |
| `--out DIR` | Write outputs and logs below `DIR` during a normal restore. |
| `--dry-run` | Development feature. Run restoration without retaining outputs or logs. |
| `--json` | Development feature. Write the structured report instead of human-readable standard output. |
| `--threads N` | Development feature. Set a positive worker cap for this run, overriding `SENBEI_THREADS`. `1` selects sequential processing. |
| `-v`, `--verbose` | Print per-stage progress. |
| `-q`, `--quiet` | Hide progress and per-file lines; repeat to suppress all standard output. |
| `--no-log` | Don't write a run log. |
| `--scan-all` | Probe every selected target-name candidate, including files too small for the default scan to open. |
| `--strict-integrity` | Not in a released build yet. Exit non-zero when any output fails the static integrity check (a suspect) or a file errors. Off by default: a suspect is still written and the process exits `0` unless a file errors. Repeat `-q` is unchanged. |
| `--max-entry-mib N` | Not in a released build yet. Android only. Positive MiB ceiling for one ZIP entry during decompression, one decoded buffer, one artifact read, and one output file. Default `2048` (1 MiB = 1,048,576 bytes). |
| `--max-total-mib N` | Not in a released build yet. Android only. Positive MiB ceiling for cumulative archive bytes across a folder, plus separately accounted extraction and restoration work inside one engine task. Default `8192`. This is not a peak-memory cap. |
| `--max-entries N` | Not in a released build yet. Android only. Positive ceiling for archive entries and stage-2 records, counted across nested archives. Default `100000`. |
| `--max-depth N` | Not in a released build yet. Android only. Nesting ceiling for nested APKs and stage-2 streams. The root is depth `0`, and `0` is allowed. Default `32`. |
| `--no-pause` | Disable the Explorer-friendly Windows exit prompt. |
| `-V`, `--version` | Print the version and exit. |
| `-h`, `--help` | Show usage. |

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | The requested restore completed without errors. A suspect output still exits `0` unless `--strict-integrity` is set. |
| `1` | A target failed, a scan probe was unreadable, or a single-file restore errored. With `--strict-integrity` (not released yet), any suspect output also exits `1`. Outputs are still written. An Android resource limit that is exceeded also exits `1`; Senbei doesn't silently truncate that work. |
| `2` | The command line was rejected. A resource-limit value that isn't an unsigned decimal integer is a command-line error, as is `0` for every limit except `--max-depth`. |
