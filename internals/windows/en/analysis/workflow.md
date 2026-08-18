---
description: "A repeatable workflow for locating stages, interpreting logs, and checking reconstructed images."
---

# Analysis workflow

This page collects methodology that has proven effective against this protection, followed by an honest list of where specific mechanisms fall short.

## Methodology

### Turn the loader's logging against itself

The most productive first step is enabling the debug log: create the per-executable 12-hex-character folder under `%temp%` (learn the name by breaking on `CreateFileW`), then run the binary. The folder's creation time must be within about two days, or that run writes no log. Every protected module narrates its own boot — status codes per stage, missing DLLs, hooked functions, addresses. Combined with the status table in [Startup sequence and status reporting](../runtime/startup-status.md#the-boot-sequence-and-status-codes), the log localizes any failure or behavior to a specific stage without any disassembly.

### Map status codes back to code

When the log is not enough, the `(code << 4) | 1` encoding turns each status code into a 2-byte pattern searchable in the binary. Searching for the word finds the exact instruction that reports that stage — an instant symbol table for the loader. This works on the on-disk loader stub and on decrypted stage buffers alike.

### Read the loader with the right expectations

- **Do not trust natural entry points.** The obvious stubs are no-op decoys (register save/restore around a timing probe). The real entry is the code that initializes the context structure — search for the unique instruction that sets up the reserved context register and follow from there.
- **Expect desynchronized disassembly.** Junk bytes after jumps and mid-instruction jump targets defeat linear sweeps; decompilers frequently bail out with "control flows out of bounds". Where static analysis stalls, emulate the stage (a CPU emulator with hooked Win32 stubs — file APIs answered from the protected file's own bytes) and capture its writes, then port the recovered primitives back to static code.
- **Compare across builds.** Loader code is bit-identical between different protected modules of the same family; only data tables differ. A cross-sample diff isolates the tables (a few hundred bytes) from the algorithm (everything else) — the fastest way to see what is per-build configuration versus code.

### Dump page-encrypted modules correctly

- A single memory snapshot captures only the demand-decrypted working set. Check the fill rate per section (a bulk-decrypted module has every page populated; page-encrypted ones show sparse, execution-driven coverage), and force every page to fault in before dumping when necessary.
- Verify the dump is post-decryption: the bytes at the true OEP should be a sane prologue (for example `48 89 5C 24 08` on x64 MSVC builds). A garbage or zero OEP region means the snapshot came too early — wait past initialization.
- Cache-manager-based forensic extractors (for example Volatility's `dumpfiles`) only see what the OS thinks is on disk; decrypted pages live in private memory and are invisible to them. Use virtual-address-space extractors (module-list or VAD-based) instead.
- Take two snapshots a few seconds apart and diff: a nonzero diff indicates background re-encryption (the re-encrypt pass at status `840`), a zero diff confirms the pages are stable.
- Time in-process helpers around the `A07` injected-thread sweep; threads spawned before the sweep may be killed. The sweep's completion is visible in the debug log.

### Verify a reconstructed image

A static unpack that reports success can still be wrong — a heuristic can choose a plausible-looking but incorrect table. Cheap structural checks catch every failure mode observed in practice:

1. `MZ` and `PE\0\0` signatures; optional-header magic `0x10B`/`0x20B`; sane section count.
2. The entry point maps to a mapped, executable, nonzero region (an all-zero entry stub is the classic "left encrypted" symptom).
3. The first import descriptor's DLL name is readable ASCII ending in `.dll` (still-ciphertext imports are the second classic symptom).
4. Managed images: COR20 header `cb == 0x48` and the metadata stream signature `BSJB`.
5. DLLs: a present base-relocation directory.

A clean report is not proof of correctness — but a failed check is a reliable "broken" signal.

