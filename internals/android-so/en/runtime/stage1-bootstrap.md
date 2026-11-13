---
description: "How the Stage 1 .init_array wrapper locates its ELF on disk, decrypts Stage 2, and transfers control."
icon: bolt
---

# Stage 1 bootstrap

One `.init_array` entry points to a `0x84`-byte register-saving wrapper in the intact `.text` head (15 `STP` instructions saving `X1`..`X30`, `MOV X0, SP`, `BL` into the bootstrap body, 15 `LDP` restores, and `RET`). The bootstrap locates its own file via `/proc/self/maps`, reads `SHT_LOUSER`, decrypts Stage 2 into anonymous memory, and jumps to its entry point.

```mermaid
flowchart TD
    A["Enter 0x84-byte .init_array wrapper\n(save X1..X30, X0 = SP)"] --> B["Compute runtime image base via ADR"]
    B --> C["Decrypt path, open & parse /proc/self/maps"]
    C --> D["Read ELF header, PHDRs, Shdrs & PT_LOAD tail"]
    D --> E["Locate SHT_LOUSER (0x80000000)"]
    E --> F["Skip 0x23C outer wrapper & decrypt 32B header"]
    F --> G["Anonymous RW mmap for Stage 2"]
    G --> H["Decrypt Stage 2 words with payload_key"]
    H --> I["Detect 4 KiB or 16 KiB page size"]
    I --> J["Flush caches (DC / IC / DSB / ISB) & mprotect"]
    J --> K["Branch to stage2_base + entry_offset"]
    B -. failure .-> X["Error stub"]
    C -. failure .-> X
    D -. failure .-> X
    E -. failure .-> X
    F -. failure .-> X
```

## Locating `SHT_LOUSER`

Stage 1 obtains its own PC with `ADR`, subtracts its link-time offset to get the loaded library's base address, decrypts `"/proc/self/maps"` into a stack buffer, opens it, and immediately wipes the path buffer. After finding the backing file path for its load base, it reads the ELF header, program headers, and section headers (`Elf64_Shdr` stride `0x40`) to locate `sh_type == 0x80000000` (`SHT_LOUSER`) after the last `PT_LOAD` segment.

Skipping the `0x23C`-byte outer wrapper reaches the `0x1000`-byte parameter area whose first 32 bytes decode under the family word constant `C` (`0xBF20165D` or `0xBF189BDD`; see [Stage 1 header](../file-format/stage1.md)).

## Stage 2 mapping and register handoff

Stage 1 allocates an anonymous writable region of `payload_size` bytes, copies and decrypts the Stage 2 image with `payload_key`, detects 4 KiB vs 16 KiB system pages, flushes data and instruction caches (`DC` / `IC` / `DSB` / `ISB`), applies `mprotect` over `protect_size`, and branches to `stage2_base + entry_offset` with eight arguments:

| Register | Value |
| --- | --- |
| `X0` | Loader context pointer |
| `X1` | Protected library's runtime image base |
| `X2` | Decrypted Stage 2 base address |
| `X3` | Decrypted Stage 2 byte size (`payload_size`) |
| `X4` | Remaining `SHT_LOUSER` stream base (4-byte-aligned end of Stage 2) |
| `X5` | Remaining `SHT_LOUSER` stream size |
| `X6` | File-tail mapping base |
| `X7` | File-tail mapping size |

Stage 2 immediately records `(X2, X3)` as module `0xE2` and `(X6, X7)` as module `0xD0`.
