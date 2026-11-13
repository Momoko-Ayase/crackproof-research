---
description: "CLI commands, inspection reports, folder and Android package handling, display languages, flags, and exit codes."
icon: terminal
---

# Usage

```text
senbei [inspect|unpack] <file|folder> [--out DIR] [-v|--verbose] [-q|--quiet]...
    [--json] [--dry-run] [--threads N] [--color auto|always|never] [--scan-all]
    [--strict-integrity] [--max-entry-mib N] [--max-total-mib N]
    [--max-entries N] [--max-depth N] [--no-log] [--no-pause]
    [-V|--version] [-h|--help]
```

`senbei <path>` is equivalent to `senbei unpack <path>`. `inspect` and `unpack` are parsed as subcommands when placed before `<file|folder>` (pass `./inspect` or `.\inspect` to target a file or folder named `inspect`).

## Common workflows

{% tabs %}
{% tab title="Unpack" %}
Write restored files below `<parent>/unpack/` (for a file) or `<root>/unpack/` (for a folder) with `.unpack` inserted before the extension, or redirect both outputs and run logs with `--out DIR`:

```cmd
senbei app.exe
senbei app.exe --out C:\out
senbei game.apk --out C:\out
senbei "C:\Games\SampleTitle"
```

For `global-metadata.dat`, Senbei writes `global-metadata.unpack.dat` only when method tokens or indices actually change; already-canonical or unsupported versions are skipped in folder runs and reported as errors on direct single-file unpacks.
{% endtab %}

{% tab title="Inspect & JSON" %}
`inspect` runs full static recovery in memory to collect research evidence without saving output files or run logs, and never executes the target:

```cmd
senbei inspect module.dll
senbei inspect module.dll --json
senbei inspect module.dll --strict-integrity --json
```

Reports include source hashes, parsed PE/ELF/metadata headers, decoded protection tables, every attempted recovery route with rejection reasons, the selected route, discovered stage parameters (distinguishing physical file offsets, companion-spliced offsets, and working-image RVAs), and static validation findings.
{% endtab %}

{% tab title="Dry run & CI" %}
`--dry-run` runs recovery and static validation without saving output files or logs (or collecting the `inspect` trace). Temporary Android extraction workspaces are cleaned up automatically:

```cmd
senbei unpack module.dll --dry-run
senbei unpack module.dll --dry-run --json --strict-integrity
senbei unpack folder --strict-integrity --no-pause -q
```

Neither `inspect` nor `--dry-run` can be combined with `--out`.
{% endtab %}
{% endtabs %}

## Android libraries and packages

Senbei restores protected AArch64 `.so` binaries (`libil2cpp.unpack.so` or `<stem>.unpack.so`) and processes `.apk`, `.apks`, and `.xapk` packages directly:

1. Reads the ZIP central directory first and follows nested `.apk` entries inside `.apks`/`.xapk` bundles up to `--max-depth`.
2. Streams only `.so` and exact `global-metadata.dat` entries to temporary files under the configured `--max-entry-mib`, `--max-total-mib`, and `--max-entries` budgets.
3. Pairs external `v24.1` metadata with the owning app's module `0x0C` (scoped by `AndroidManifest.xml` package + version across split APKs, or `<root>/lib/<abi>/` + `<root>/assets/`), unwraps slim `v24` XOR blobs into `global-metadata.unpack.dat`, and deduplicates identical loose and packaged files.

## Folder scanning and companions

Folder mode walks subdirectories recursively while pruning `unpack` directories (case-insensitively, unless the root target itself is named `unpack`) and skipping NTFS reparse-point subdirectories below the root:

* **Scanned target names (case-insensitive):** `.exe`, `.dll`, `.so`, `global-metadata.dat`, `.apk`, `.apks`, and `.xapk`. Sibling split `.apk` files sharing a manifest package and version are grouped automatically. Candidates smaller than `4,128` bytes are skipped without opening unless `--scan-all` (or `SENBEI_SCAN_ALL`) is set.
* **Windows `._` companions:** sibling `.exe._` and `.dll._` files are consumed by their matching stub rather than counted as skipped files. Managed companion DLLs require both `Module.dll` and `Module.dll._` so Senbei can overlay the stub's `COR20` tables onto the decrypted IL method bodies.

{% hint style="info" %}
**Companion diagnostics.** `Missing companion file` is reported only when a PE32+ entry record explicitly carries the `._` companion declaration (`~0x1000` and `~"._\0\0"`) and `<input>._` is absent. `Companion doesn't match` means `<input>._` is shorter than 32 bytes or its `0x00..0x20` header differs from `stub[0x1000..0x1020]`.
{% endhint %}

## Display language and terminal colors

Senbei supports five display languages: `en` (English), `zh-CN` (Simplified Chinese), `zh-TW` (Traditional Chinese), `ja` (Japanese), and `ko` (Korean).

{% tabs %}
{% tab title="Command Prompt" %}
```cmd
set SENBEI_LANG=ja
senbei inspect module.dll
```
{% endtab %}

{% tab title="PowerShell" %}
```powershell
$env:SENBEI_LANG = "zh-TW"
senbei inspect module.dll
```
{% endtab %}

{% tab title="POSIX / Bash" %}
```sh
SENBEI_LANG=ko senbei inspect module.dll
```
{% endtab %}
{% endtabs %}

* **Locale resolution:** `SENBEI_LANG` strips `.encoding` and `@modifier` suffixes, matches case-insensitively with `-` or `_`, and gives script subtags (`Hans` / `Hant`) priority over regions (`zh-Hans-HK` -> Simplified Chinese; `zh-Hant`, `zh-TW`, `zh-HK`, `zh-MO` -> Traditional Chinese). When `SENBEI_LANG` is unset, Senbei checks the Windows UI language list or `LC_ALL` / `LC_MESSAGES` / `LANG` / `LANGUAGE`, falling back to English.
* **What stays English:** `--json` output, saved `.log` files, `inspect` structural evidence tables, and `-v` stage detail lines always stay in English; when a localized error summarizes a more detailed internal error, the full English detail prints on the next line.
* **Colors (`--color MODE` or `--color=MODE`):** `auto` (default) checks TTY status per stream and disables colors when `NO_COLOR` is non-empty or `TERM=dumb`; `always` forces ANSI colors in human-readable output; `never` disables them. `--json` and `.log` files never contain ANSI escapes.

## Static validation and browser limits

Static validation checks restored PE headers, section mappings, entry-point reachability and CRT branch targets, up to 256 import descriptors, native data directories, and CLR `BSJB` streams, alongside Android ELF `PT_LOAD` bounds, dynamic tables, symbol hashes, relocations, and constructor pointers. Outputs with structural warnings or non-fatal errors are still written during `unpack` and counted as `suspect`; `--strict-integrity` turns any `suspect` result (in `unpack`, `--dry-run`, or `inspect`) into exit code `1`.

In the WebAssembly browser app, **Input limit per module (MiB)** defaults to `256` (`8`..`4096` MiB, counting a stub and its `._` companion together before reading them into memory), and **Export JSON** downloads a local `senbei.browser-report` v1 file. Android `.so` and package restoration require native `senbei` or `senbei-gui`.

## Flags reference

| Flag | Behavior |
| --- | --- |
| `--out DIR` | Write unpacked files and run logs under `DIR` (`unpack` mode only). |
| `--dry-run` | Run recovery and validation without saving output files or logs. |
| `--json` | Emit a versioned JSON report on `stdout` (even with `-q -q`); disables run logs and exit pause. |
| `--threads N` | Worker thread limit (`N >= 1`), overriding `SENBEI_THREADS` (`1` runs sequentially). |
| `--color auto\|always\|never` | Control ANSI terminal colors (`--color=MODE` also accepted). |
| `-v`, `--verbose` | Print per-stage progress lines. |
| `-q`, `--quiet` | Hide banner/per-file progress; pass `-q -q` (separate flags) to silence all `stdout` and runtime `stderr`. |
| `--no-log` | Skip writing `senbei-YYYYMMDD-HHMMSS.log`. |
| `--scan-all` | Probe target-named files smaller than `4,128` bytes during folder scans. |
| `--strict-integrity` | Exit `1` if any recovered image is marked `suspect` (applies to `unpack`, `--dry-run`, and `inspect`). |
| `--max-entry-mib N` | Maximum size in MiB (`N >= 1`) per Android ZIP entry, decoded container, artifact, or output file (default `2048`). |
| `--max-total-mib N` | Maximum cumulative MiB (`N >= 1`) for Android archive extraction and per-task recovery (default `8192`). |
| `--max-entries N` | Maximum archive entries and Stage 2 records (`N >= 1`) across nested Android archives (default `100000`). |
| `--max-depth N` | Maximum nesting depth (`0` allowed) for nested Android APKs and Stage 2 streams (default `32`). |
| `--no-pause` | Skip the interactive exit prompt when launched from Windows Explorer. |
| `-V`, `--version` / `-h`, `--help` | Print version or usage help and exit `0`. |

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Command succeeded (`unpack`, `--dry-run`, `inspect`, `--help`, or `--version`), with no target errors (and no `suspect` outputs when `--strict-integrity` is set). |
| `1` | One or more targets failed, a scan/file probe was unreadable, an Android resource limit was exceeded, or `--strict-integrity` encountered a `suspect` image. |
| `2` | Invalid command-line arguments (including invoking `senbei` with no arguments, incompatible flags, or invalid numeric limits). |
