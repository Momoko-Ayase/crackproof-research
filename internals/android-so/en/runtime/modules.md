---
description: "Observed roles of runtime modules, listed by identifier."
---

# Runtime modules

Command identifiers below come from stage 2 records. Roles are taken from the functions those modules run after they are materialized. Identifiers required for ELF restoration stay on [Module streams](../restoration/module-streams.md). Environment and integrity behavior is collected on [Environment and integrity checks](environment-checks.md).

An identifier listed as “not reduced” was present as a record; its behavior has not been turned into a stable description.

## Interpreters and handoff

| ID | Role |
| --- | --- |
| `0xE2`–`0xE8` | Nested record-stream interpreters. `0xE2` is stage 2 itself |
| `0xF3`–`0xF8` | Direct data objects that feed the next interpreter |
| `0xD0` | File-tail mapping handed over from stage 1 |
| `0x98` | Final handoff: copies the restored image and invokes `.init_array`. Corresponds to Windows status `280` |

## Restoration

| ID | Role |
| --- | --- |
| `0x9B` | Restore workflow: page permissions, consume `0x9D` and `0x9E` |
| `0x9D` | Protected container: descriptors, segments, writer streams |
| `0x9E` | Hidden dynamic-symbol patches (`dynsym` / `dynstr`) |
| `0xB9` | Metadata-related data. A real payload on IL2CPP libraries; empty or data-less on some native libraries |
| `0x0C` | IL2CPP only. Replaces `mmap` with a hook that restores method tokens when `global-metadata.dat` is mapped. See [Method tokens](../metadata/method-tokens.md) |

## Environment and integrity

| ID | Role |
| --- | --- |
| `0x81` | Decrypt a library name and symbol, `dlopen` / `dlsym`, cache the pointer |
| `0x96` | 16-byte block transform used as a general decryptor |
| `0x8F` | Read `/proc/self/cmdline`, query uid/gid/tid, create or reuse an environment token, check path owner and mode |
| `0x97` | Scan `/proc` for same-uid processes; `mprotect` around code writes; start a detached worker thread |
| `0x02` | UDP port 123 time query, then compare the reply with a configured threshold |
| `0x69` | `fork` a child probe and wait for its exit status |
| `0x60` | Scan system library directories, `/proc` environment, and runtime paths |
| `0x40` | Check `base.apk` and sibling split APKs. Signature order: v3.1, then v3, then v2, then JAR/v1 |
| `0x20` | Validate a target path, ELF header, `/proc/self/maps`, and a libc mapping |
| `0x33` | Build a dex2oat option list and delete artifacts that do not match it |
| `0x72` | Unix-domain socket `bind` / `listen` / `accept` |
| `0xB0` | Transform a sentinel table |

## Present, not reduced

`0x8E`, `0x6A`, `0x68`, `0x54`, `0x71`, `0x53`, `0xA4`, `0x58`, `0x73`, `0xA0`, `0xB2`.

These appear in the same interpreter layers as the rows above. They are registered and, unless `flags & 0x100`, receive init/entry calls. Their functions have not been reduced beyond that.
