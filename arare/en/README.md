---
description: "A source-built Windows PE protector that reproduces observed CrackProof layout families."
icon: shield-halved
---

# Arare

Arare is a source-built Windows PE protector. It compiles its own native and managed loaders and generates per-build keys, AES schedules, bytecode programs, Huffman/LZ compression tables, and stage metadata without commercial donor binaries or extracted stub profiles.

Native protection covers x86 and x64 EXEs and DLLs across four structural families (`pe32`, `pe64-classic`, `pe64-modern`, and `legacy-dll`). Managed protection wraps IL assemblies with generated ECMA-335 startup types and an independent native decoder. Compatibility is verified against unchanged Senbei 1.3.1 and by executing original, protected, and unpacked programs on Windows 11 build 26100 (targeting Windows 10 and Windows 11).

The embedded runtime implements per-build `%TEMP%`-gated debug logging, configurable environment checks inside manually mapped helper DLLs, page encryption with on-fault decryption (`KiUserExceptionDispatcher`), seeded loader-code variation, and post-startup metadata erasure. Failed checks write an `AAA-BBB-CCC` closing code to active logs; native EXEs raise `EXCEPTION_ACCESS_VIOLATION` before terminating by default (`--antidebug-av=on`) so attached debuggers break, while DLLs, `--antidebug-av=off` native EXEs, and managed modules call `TerminateProcess` directly.

For the underlying formats, see [CrackProof for Windows internals](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/). Static unpacking is documented in [Senbei](https://app.gitbook.com/s/ul1YGOqMPNVceXYP7FFj/).

## In this section

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-terminal"></i></td><td><strong>Usage</strong></td><td>CLI <code>protect</code>, <code>inspect</code>, and <code>verify</code> commands, profiles, environment checks, page encryption, and debug logs.</td><td><a href="usage.md">Usage</a></td></tr><tr><td><i class="fa-window-maximize"></i></td><td><strong>GUI</strong></td><td>WPF front-end for batch job queues, per-row profile and check overrides, PowerShell export, and verification.</td><td><a href="gui.md">GUI</a></td></tr><tr><td><i class="fa-circle-check"></i></td><td><strong>Support</strong></td><td>Supported native and managed families, tested CLR hosts, pack-time refusals, and structural limits.</td><td><a href="support.md">Support</a></td></tr><tr><td><i class="fa-diagram-project"></i></td><td><strong>Design</strong></td><td>Crate boundaries, store-once section and resource encoding, three-phase runtime startup, and remaining commercial gaps.</td><td><a href="design.md">Design</a></td></tr><tr><td><i class="fa-hammer"></i></td><td><strong>Development</strong></td><td>Building native loaders and managed tools, running the Senbei 1.3.1 oracle, and workspace conventions.</td><td><a href="development.md">Development</a></td></tr></tbody></table>

## Scope and licenses

Android targets, standalone IL2CPP `global-metadata.dat` obfuscation, and kernel driver options in `protect` are out of scope (an experimental kernel provider lives separately under `kernel/`).

{% hint style="info" %}
**Licensing split.** Host tooling (`arare-cli`, `arare-engine`, `tools/managed`, `gui`, and `verification/senbei-oracle`) is `AGPL-3.0-only`. The PE parser (`arare-pe`), codecs (`arare-codec`), and all embedded native and managed runtime code (`arare-runtime`, `runtime/`) are `MIT`, so no AGPL code is embedded into protected binaries.
{% endhint %}
