---
description: "Workspace layout, encoding contract, and usermode runtime behavior."
---

# Design

Arare generates protected Windows PE files and builds its own embedded loader. Byte-identical commercial output is not a target. Compatibility is described by structural layout families and verified behavior.

## Workspace

| Component | Responsibility | License |
| --- | --- | --- |
| `arare-pe` | Immutable checked PE model and disk-to-image mapping | MIT |
| `arare-codec` | Rolling transforms, AES, byte programs, Huffman/LZ | MIT |
| `arare-engine` | Profile graphs, Windows loader placement, managed orchestration | AGPL-3.0-only |
| `arare-runtime`, `runtime/src`, `runtime/arch` | Independently built native reconstruction and startup | MIT |
| `runtime/managed` | Managed before-JIT initialization and memory adapters | MIT |
| `tools/managed` | Source-written ECMA-335 metadata/wrapper generation | AGPL-3.0-only |
| `arare-cli` | Input/output, options, diagnostics, and publication | AGPL-3.0-only |

A separate `verification/senbei-oracle` crate links unchanged Senbei only for tests. Normal builds do not resolve a sibling Senbei checkout. Copied AGPL source cannot enter the runtime dependency graph.

The engine API is `protect(input: &[u8], options: &Options) -> Result<Artifact, Error>`. `Options` selects an applicable `Profile`, compression, a seed, and embedded or companion storage. A fixed explicit seed reproduces an Arare output for tests; ordinary packing obtains fresh randomness from the OS.

Stages are encoded in the reverse order of their checksum and key dependencies. Table sizes grow from actual input data. The runtime consumes the same representation that Senbei recovers. Private reconstruction trailers understood only by Arare are not a substitute for format compatibility.

The four families — PE32, classic PE32+, modern marker-less PE32+, and legacy DLL — have different discovery, stage, metadata, and finish rules. Family names describe layout, not invented commercial versions.

## Runtime

Two source-built helper DLLs are embedded in every protected build, decrypted in memory, and manually mapped. The mapped image's MZ/PE magics are zeroed; the module never joins the PEB list. This mirrors the observed HtpecIt/HtdpStub2 split under Arare-native names.

Checks run in the observed order. Phase one runs before the protected file is read (410, 510, 520, 52F, 540). Phase two runs after the file is staged (A03, C00, B00, C01, A09, A11, A0F, BD0, A04 or A08, optional BE0, A07/A01). Native DLLs with `host-process` enabled then log `A15` as a sequencer marker with no check body. Phase three, after page sealing, runs optional E55/E91 device observations.

`A15` is a marker, not a check. Host executables never log it. `A11` in Arare uses cooperative host identity (native `.arldr` / managed `.armclr` markers plus an optional stamp). Commercial artifacts scan for a `peC` section or an exact-case `KeRnEl32.dLl` import; that spoofability is accepted.

A DLL inherits its invoker EXE's `%TEMP%` debug-log gate and folder, including when the seeds differ. An available host context always takes precedence, even when its gate is closed or stale. `--check host-process=off` does not disable that inheritance.

Page-encrypted builds re-encrypt executable application pages in place after reconstruction and set them to `PAGE_NOACCESS`. The handler is installed by patching `ntdll!KiUserExceptionDispatcher`. Compatible modules register with one process dispatcher. Writable executable sections are rejected when page encryption is effectively on.

After status `280`, native startup clears spent import maps, helper blobs, source page tables, and one-shot config. Geometry needed by later notifications and retained host identity survive. Demand-decrypt programs remain available for subsequent faults.

## Kernel

`kernel/` is an independently authored experimental provider. Ordinary `protect` has no kernel option. Ordinary Cargo builds do not require the WDK. Effectiveness claims require actual kernel execution evidence, not host doubles or a successful WDK build.

## Remaining gaps

Implemented usermode menu covers 410, 510, 520, 52F, 540, A03, C00, C01, BD0, B00, A09, A0F, A07/A01, A11, A08, A04, BE0, E55, E91, plus A15, page encrypt, scribble, and optional ErrLog-Pec. Remaining commercial-fidelity work includes host-directory admission, unidentified E-series objects, loaded-module integrity cadence, a verified commercial default matrix, and a separate Windows 10 execution run. Interoperability with commercial CrackProof hosts is a separate milestone.
