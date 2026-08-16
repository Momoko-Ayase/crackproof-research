---
description: "Methodology for analyzing protected binaries, plus a catalogue of observed weaknesses in the protection."
---

# Reverse engineering notes

This page collects methodology that has proven effective against this protection, followed by an honest list of where specific mechanisms fall short.

## Methodology

### Turn the loader's logging against itself

The most productive first step is enabling the debug log: create the per-executable 12-hex-character folder under `%temp%` (learn the name by breaking on `CreateFileW`), then run the binary. Every protected module narrates its own boot — status codes per stage, missing DLLs, hooked functions, addresses. Combined with the status table in [Runtime behavior](runtime-behavior.md#the-boot-sequence-and-status-codes), the log localizes any failure or behavior to a specific stage without any disassembly.

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

## Observed weaknesses

For completeness and future research, the mechanisms that demonstrably fall short:

**The VM checks are bypassable by configuration alone.** The registry check matches vendor strings only at the *start* of the BIOS/product values, while at least one major hypervisor places its marker at the *end* of its BIOS version — setting `SMBIOS.reflectHost = "TRUE"` hides it entirely. The VMware backdoor probe is neutralized by `monitor_control.restrict_backdoor = "TRUE"` (and by not installing guest tools), and other hypervisors allow overriding SMBIOS strings directly.

**The debug log is a self-documenting loader.** The status-code design that helps the vendor's support also hands the analyst a stage-by-stage execution trace and a 2-byte search pattern per stage. The mailslot channel is encrypted, but the file log is not.

**Page encryption yields to in-process readers.** The demand-decrypt handler services faults from any thread in the same process, so a helper inside the process can touch every page and copy the decrypted bytes. The anti-dump scribble is reversible, and on builds where it is disabled the pages are clean.

**The kernel drivers weaken the host.** Generation 1 exposes unauthenticated kernel shellcode execution to any process. Generation 2's PID-encryption "authentication" grants its `EPROCESS`-write primitive to any program that reproduces it — a signed BYOVD — and the Protected Process flag it sets can be toggled off with kernel-level access or absorbed by injecting before it is set. Only generation 3 avoids granting attackers new powers.

**The tamper-evidence chain is fully recomputable.** Every transform in the container is reversible (XOR chains, rotations, a permutation bytecode, CBC-mode AES with an embedded schedule) and every checksum is a standard CRC-32 over knowable bytes. Nothing in the design requires a secret held outside the file. Consequently the checksum chain detects naive patching but cannot prevent it: an analyst who modifies the payload can recompute every chained key and re-embed the result, and the loader will accept it. The chain raises the cost of modification; it does not bound it.

**Process-policy checks are coarse.** The parent-process policy (`A03`) is satisfied by launching from an approved parent, and the DLL host check (`A11`) keys on artifacts (a `peC` section, mixed-case `KeRnEl32.dLl` imports) that identify only unmodified hosts.

None of these make the protection trivial — the layered design still costs real effort to analyze end-to-end — but each is a documented, reproducible gap rather than a theoretical one.
