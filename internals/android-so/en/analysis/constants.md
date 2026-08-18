---
description: "Observed Android format constants and the scope in which each is valid."
---

# Constants

These values are observations from the current Android SO samples. They help identify a build family but do not replace structural checks.

| Value | Scope |
| --- | --- |
| ELF64, little-endian, AArch64 | File architecture |
| One `SHT_LOUSER` section | Private-section recognition |
| `0x23c` (572) | Observed stage 1 outer wrapper |
| `0x1000` | Encrypted parameter area after the wrapper; first 32 bytes are the word header |
| `0xbf20165d`, `0xbf189bdd` | Observed stage 1 word constants (one per family) |
| `0x94511dd2` / `0x579357eb` | GF(2³²) multiplier / reduction polynomial |
| `00 01 0e 00` | AES-256 schedule marker (bits `0x0100`, 14 rounds) |
| `0xE2` | Initial stage 2 stream identifier |
| `0x5c` | Stage 2 record and protected descriptor size |
| `0x1800` / `0x18` | Stage 2 module table size / entry size (256 slots) |
| `0xD0` | File-tail mapping registered at stage 2 start |
| `0xF3`–`0xF8` / `0xE3`–`0xE8` | Direct data objects and their child interpreters |
| `0x9B`, `0x9D`, `0x9E` | Required restoration modules |
| `0x0C` | IL2CPP-only `mmap` hook for method tokens |
| `0xa6fae968` | Observed default method-token seed from module `0x0C` |
| `0x98` | Handoff that invokes the restored `.init_array` |
| `0xFAB11BAF`, version `31` | Recognized IL2CPP metadata |
| `lib__XXXX__.so`, `assets/<id>/data1.dat` | Companion protector library and side configuration |

When a sample differs, record the new value with its source and re-run all range and relationship checks. Do not widen a parser merely to make an isolated constant fit.
