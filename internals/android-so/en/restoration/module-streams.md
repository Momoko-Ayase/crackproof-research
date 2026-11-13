---
description: "Required and optional Stage 2 module artifacts consumed during static ELF and metadata restoration."
icon: route
---

# Module streams

Stage 2 stream extraction begins at root stream `0xE2` (which registers itself as `0xE2` and the `SHT_LOUSER` file-tail mapping as `0xD0` in its 256-slot runtime table) and recursively decodes every container and nested interpreter stream (`0xE3`..`0xE8` fed by `0xF3`..`0xF8`).

## Static restoration modules

Every protected library contains runtime environment and integrity modules alongside the restoration payload. Static reconstruction uses three required modules and up to three optional ones:

| Module | Requirement | Static restoration role |
| --- | --- | --- |
| `0x9B` | Required | Supplies `header_seed`, `container_seed`, the reversed AES-256 round-key schedule, and `skip_aes` |
| `0x9D` | Required | Supplies the `ProtectedDescriptor`, the primary `PT_LOAD` writer container, and the auxiliary relocation/symbol container |
| `0x9E` | Required | Supplies hidden `.dynsym` entries and `.dynstr` names stripped from the on-disk ELF |
| `0x96` | Optional | Supplies `auxiliary_symbol_seed` to undo the per-row symbol-index rotation in `0x9D`'s auxiliary relocation tables |
| `0x98` | Optional | Emulated with a bounded AArch64 control-flow and integer interpreter to recover real `.init_array` constructors and prune `RET`-only placeholders |
| `0x0C` | Optional (IL2CPP `v24.1`) | Supplies the `methodIndex` permutation seed and 256-entry exception table for external `v24.1` `global-metadata.dat` |

## Duplicate and non-restoration records

* **Runtime-only modules:** records for environment probes, import helpers, or unclassified identifiers (`0x8F`, `0x97`, `0x81`, `0x40`, `0x8E`, and others listed in [Runtime modules](../runtime/modules.md)) are decoded and validated during stream traversal, then ignored during ELF reconstruction.
* **Idempotent duplicates:** if two records produce the same `command_id` with identical SHA-256 digests, extraction keeps a single copy; if their digests differ, extraction fails rather than guessing which payload wins.
* **Missing baseline modules:** if any of `0x9B`, `0x9D`, or `0x9E` is absent after stream traversal completes, ELF restoration aborts without writing an output file.
