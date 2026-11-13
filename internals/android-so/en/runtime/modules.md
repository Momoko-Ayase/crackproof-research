---
description: "Catalog of Stage 2 module identifiers across stream interpreters, ELF/metadata restoration, and runtime checks."
icon: layer-group
---

# Runtime modules

Stage 2 records register modules by a 1-byte `command_id` (`0x00`..`0xFF`). Static restoration uses the modules documented in [Module streams](../restoration/module-streams.md); the remaining modules run load-time checks or helper services.

## Stream interpreters and bootstrap slots

| ID | Role |
| --- | --- |
| `0xE2`..`0xE8` | Nested record-stream interpreters (`0xE2` is the decrypted Stage 2 root image) |
| `0xF3`..`0xF8` | Direct stream slices passed as input to `0xE3`..`0xE8` (`sid = command_id - 0x10`) |
| `0xD0` | `SHT_LOUSER` file-tail mapping registered by Stage 2 from `(X6, X7)` |

## Image, symbol, constructor, and metadata restoration

| ID | Role |
| --- | --- |
| `0x9B` | Restoration coordinator holding `Module9bConfig` (`header_seed`, `container_seed`, reversed AES-256 round keys, `skip_aes`); restores target segments and permissions |
| `0x9D` | Direct payload holding the `0x5C` `ProtectedDescriptor`, the primary `PT_LOAD` container, and the auxiliary relocation/symbol container |
| `0x9E` | Hidden `.dynsym` symbols and `.dynstr` strings stripped from the visible ELF |
| `0x96` | 16-byte block decryptor holding `auxiliary_symbol_seed`, used to unpermute auxiliary relocation symbol indices |
| `0x98` | Final constructor dispatcher: resolves and invokes the target library's `.init_array` callbacks after image restoration (analogous to Windows status `280`) |
| `0x0C` | IL2CPP builds only: hooks `mmap` to deobfuscate `global-metadata.dat` at load time, and embeds the `v24.1` `methodIndex` seed plus 256-entry exception table |
| `0xB9` | Auxiliary metadata-related blob (populated on IL2CPP builds; absent or empty on plain native libraries) |

## Environment, symbol lookup, and integrity helpers

| ID | Role |
| --- | --- |
| `0x81` | Decrypts library and symbol names, resolves pointers via `dlopen` / `dlsym`, and caches them |
| `0x8F` | Reads `/proc/self/cmdline`, queries `uid`/`gid`/`tid`, manages an environment token, and checks path ownership/mode |
| `0x97` | Scans `/proc` for same-UID processes, brackets code writes with `mprotect`, and launches a detached monitor thread |
| `0x02` | Sends a UDP port-123 NTP time query and checks the response against a threshold |
| `0x69` | `fork`s a probe child process and checks its exit status |
| `0x60` | Scans system library folders, `/proc` environment variables, and runtime paths |
| `0x40` | Validates `base.apk` and split APK signatures (v3.1 -> v3 -> v2 -> v1/JAR) |
| `0x20` | Verifies target file paths, ELF headers, `/proc/self/maps`, and the `libc` mapping |
| `0x33` | Builds a `dex2oat` option list and removes non-matching oat/art artifacts |
| `0x72` | Opens and accepts connections on a Unix-domain socket (`bind` / `listen` / `accept`) |
| `0xB0` | Transforms an internal sentinel table |

<details>
<summary>Additional observed module IDs (unclassified)</summary>

`0x8E`, `0x6A`, `0x68`, `0x54`, `0x71`, `0x53`, `0xA4`, `0x58`, `0x73`, `0xA0`, `0xB2`.

These identifiers appear in nested Stage 2 streams alongside the modules above, register in the 256-slot table, and run `init`/`entry` callbacks unless `flags & 0x100` is set. Static ELF restoration does not depend on them.
</details>
