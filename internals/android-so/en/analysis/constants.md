---
description: "Summary of observed Android ELF64, cipher, Stage 2 module, relocation, and IL2CPP metadata constants."
icon: sliders
---

# Constants

The tables below list format constants observed across analyzed CrackProof Android AArch64 builds. Structural bounds and cross-table checks take precedence over any single constant.

## ELF and Stage 1

| Constant | Scope |
| --- | --- |
| ELF64, little-endian, `EM_AARCH64` (`183` / `0xB7`) | Required file class, endianness, and architecture (`e_phentsize = 0x38`, `e_shentsize = 0x40`) |
| `SHT_LOUSER` (`0x80000000`) | Single trailing private payload section at 16-byte-aligned `PT_LOAD` file end |
| `0x84` bytes (`15 × STP` .. `15 × LDP; RET`) | Stage 1 bootstrap register-saving wrapper referenced from `.init_array` |
| `0x23C` (572) | Observed Stage 1 outer wrapper size (`outer_size`) |
| `0x1000` / `0x20` | Stage 1 parameter area size / 8-dword Stage 1 word header size |
| `0xBF20165D`, `0xBF189BDD` | Observed Stage 1 word-cipher constants `C` (one per family) |
| `lib__XXXX__.so`, `assets/<id>/data1.dat` | Companion protector stub library and per-library configuration blob |

## Ciphers, containers, and Stage 2 streams

| Constant | Scope |
| --- | --- |
| `0x94511DD2` / `0x579357EB` | GF(2³²) fixed multiplier / reduction polynomial in `gf32_mul_fixed` |
| `00 01 0e 00` | `Module9bConfig` schedule marker (flags `0x0100`, 14 AES-256 rounds, `0xF0` round-key bytes) |
| `0xE2` | Root Stage 2 interpreter stream ID |
| `0xE3`..`0xE8` / `0xF3`..`0xF8` | Nested interpreter modules and their direct input stream slices (`sid = command_id - 0x10`) |
| `0xD0` | `SHT_LOUSER` file-tail mapping slot registered at Stage 2 entry |
| `0x1800` / `0x18` | Stage 2 runtime module table size / slot stride (256 slots) |
| `0x5C` (23 dwords) | Stage 2 record descriptor and `0x9D` `ProtectedDescriptor` byte size |
| `0x2` / `0x100` | Descriptor `DIRECT_FLAG` (raw slice) / skip `init` and `entry` callbacks flag |
| `0x1B00` | Maximum Huffman-table byte size (`tree_size`) in `ContainerHeader` |

## Static restoration and IL2CPP metadata

| Constant | Scope |
| --- | --- |
| `0x9B`, `0x9D`, `0x9E` | Required baseline ELF restoration modules (config, primary+auxiliary containers, hidden symbols) |
| `0x96`, `0x98`, `0x0C` | Optional static restoration modules (auxiliary symbol seed, `.init_array` constructor interpreter, `v24.1` metadata seed + exception table) |
| `0x403`, `0x101`, `0x401`, `0x402` | Auxiliary AArch64 relocation types: `RELATIVE`, `ABS64`, `GLOB_DAT` (`relocation1`), and `JUMP_SLOT` (`relocation2`) |
| `0xD65F03C0` (`RET`) | Placeholder `.init_array` target pruned when `0x98` constructor recovery runs |
| `0xFAB11BAF`, versions `24` (`v24.1`), `29`, `31`, `39` | Observed external IL2CPP metadata magic and layouts |
| `0xA6FAE968` | Default MethodDef permutation seed observed in module `0x0C` |
| `0x2701F30`, `[0x9732CA38, 0xBAC4374F]` | Embedded XOR-wrapped slim v24 metadata size and unwrapped byte-swapped header probe dwords |
