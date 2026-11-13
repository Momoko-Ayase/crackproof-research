---
description: "Static unpacker and inspector for CrackProof-protected Windows PE files, Android AArch64 libraries, and IL2CPP metadata."
icon: screwdriver-wrench
---

# Senbei

Senbei (`1.4.0`) is a static unpacker and structural inspection tool for CrackProof-protected binaries. It recovers and validates binaries from individual files, Android app packages, and directories without executing or attaching to the target.

Native releases for Windows and Linux include both the `senbei` command-line tool and the `senbei-gui` desktop workbench, localized in English, Simplified Chinese, Traditional Chinese, Japanese, and Korean. A WebAssembly build of the same core engine runs locally in the browser for loose Windows PE and metadata files.

## Supported inputs

* **Windows PE (`PE32` and `PE32+`):** protected `.exe` and `.dll` modules (native and managed .NET), including external `.exe._` and `.dll._` companion payloads.
* **Android native libraries (`ELF64` AArch64):** standalone protected `.so` files and `.apk`, `.apks`, or `.xapk` app packages.
* **Unity IL2CPP metadata:** `global-metadata.dat` files across Windows `-GMD` (`v31`) and Android seeded (`v24.1`, `v29`, `v31`, `v39`) or embedded XOR (`v24`) layouts.

The underlying container formats and transforms are documented in [CrackProof for Windows internals](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/) and [CrackProof for Android SO internals](https://app.gitbook.com/s/fcBZibCo72OSh5jVcKoo/).

## In this section

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-terminal"></i></td><td><strong>Usage</strong></td><td>CLI commands (<code>unpack</code>, <code>inspect</code>, <code>--dry-run</code>, <code>--json</code>), folder and package rules, display languages, flags, and exit codes.</td><td><a href="usage.md">Usage</a></td></tr><tr><td><i class="fa-window-maximize"></i></td><td><strong>GUI</strong></td><td>Native desktop workbench (<code>senbei-gui</code>): visual batch queue, research inspector, Hex + RVA viewer, PE Compare, and settings.</td><td><a href="gui.md">GUI</a></td></tr><tr><td><i class="fa-diagram-project"></i></td><td><strong>Design</strong></td><td>Nine-crate workspace layout, profile and trace architecture, Windows and Android pipelines, and WebAssembly boundaries.</td><td><a href="design.md">Design</a></td></tr><tr><td><i class="fa-hammer"></i></td><td><strong>Development</strong></td><td>Building CLI, desktop GUI, and WebAssembly targets, running corpus/fuzz/parity suites, benchmarks, and environment variables.</td><td><a href="development.md">Development</a></td></tr></tbody></table>

## Interfaces at a glance

| Surface | Supported targets | Output & reporting |
| --- | --- | --- |
| `senbei` (CLI) | Loose files, folders, `.apk`/`.apks`/`.xapk` | Restored files, run logs, colored terminal output, `--json` schema v1 reports |
| `senbei-gui` (Desktop) | Loose files, folders, `.apk`/`.apks`/`.xapk` | Restored files, interactive `Overview`/`Research`/`Hex`/`Compare`/`Entries`/`Log`, JSON & text report export |
| Browser (`web/`) | Loose Windows PE files (with `._` companions) & `global-metadata.dat` | Local in-browser download and `Export JSON` report (inputs never leave the device) |
