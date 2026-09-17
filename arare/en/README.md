---
description: "A source-built Windows PE protector that reproduces observed CrackProof layout families."
---

# Arare

Arare is a source-built Windows PE protector. It generates its own loader, keys, AES schedules, byte programs, compression tables, and stage metadata. There are no commercial donor executables or extracted stub profiles.

Native protection covers x86 EXEs/DLLs and x64 EXEs/DLLs through the PE32, classic PE32+, modern PE32+, and legacy-DLL families. Managed protection uses readable IL entry wrappers and an independent native decoder. Compatibility is checked against unchanged Senbei and by executing generated original, protected, and recovered programs. Commercial byte identity is not a target.

Windows 10 and Windows 11 are the target platforms. Current execution evidence is Windows 11 build 26100. Runtime behavior follows the observed CrackProof pipeline: per-build gated debug logging with original status codes, configurable environment and anti-analysis checks running from manually mapped support modules, demand-decrypt page encryption, seeded loader-code variation, and erasure of spent runtime metadata. Check failures terminate silently with `AAA-BBB-CCC` failure codes.

The protection formats and runtime behavior behind these outputs are documented in [CrackProof for Windows internals](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/). Senbei, the project's static unpacker, is documented in [Senbei](https://app.gitbook.com/s/ul1YGOqMPNVceXYP7FFj/).

Android, kernel components as a packer option, and standalone IL2CPP metadata obfuscation are deferred. An experimental kernel provider exists in the source tree; it is not a `protect` option.

## In this section

| Page | What it covers |
| --- | --- |
| [Usage](usage.md) | Command-line protect, inspect, and verify |
| [GUI](gui.md) | WPF front-end that builds the same command lines |
| [Support](support.md) | Tested families, hosts, and explicit refusals |
| [Design](design.md) | Workspace layout, encoding, and runtime contract |
| [Development](development.md) | Building, testing, and contributing |

## Licenses

The CLI, format orchestration, and managed metadata writer are AGPL-3.0-only. The PE model, codec implementations, and independently written native and managed runtime are MIT. The AGPL metadata writer is not embedded in protected applications. Senbei is a read-only test reference and is excluded from ordinary workspace builds.
