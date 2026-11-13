---
description: "Step-by-step workflow for capturing debug logs, mapping stage code, dumping pages, and validating restored PEs."
icon: list-check
---

# Analysis workflow

{% stepper %}
{% step %}
## Capture the per-build `%temp%` debug log

Break on or trace `CreateFileW` at process start to observe the 12-hex-character directory probed under `%temp%`, create that folder (its creation timestamp must be within roughly 48 hours), and re-run the binary. Every protected EXE and DLL writes a stage-by-stage trace (`HHMMSSmmmE-...` / `HHMMSSmmmD-...`) ending with an `AAA-BBB-CCC` closing summary (see [Startup sequence and status reporting](../runtime/startup-status.md#the-boot-sequence-and-status-codes)).
{% endstep %}

{% step %}
## Map status codes to host and helper code

The logging helper receives a 32-bit packed value in `ECX` whose low 16 bits encode `(code << 4) | 1` for stage status, `| 3` for `CCC` cause codes, and `| 5` for `BBB` sub-stages. Core bootstrap codes (`200`, `560`, `590`, `5A0`, `5E1`, `5E2`, `800`) appear inside the host module's loader section before post-execution scrubbing, whereas `410`/`510`/`520`/`540`, `Cxx`, and `Axx` immediates live inside the manually mapped helper DLLs (`HtpecIt.dll`, `dm`, etc.).
{% endstep %}

{% step %}
## Separate polymorphic decoys from real stage code

* Skip obvious register-saving timing decoys (`in eax, dx` followed by `jne $+2` with zero displacement) and `TF` (`#DB`) SEH traps; trace from the instruction that initializes the reserved context register instead.
* Where junk bytes after unconditional jumps desynchronize static disassembly, emulate the stage with file I/O (`CreateFileW` / `MapViewOfFile`) backed by the on-disk binary, or diff two protected modules from the same build family to isolate per-build data tables from shared stage code.
{% endstep %}

{% step %}
## Dump page-encrypted modules across VADs

* Use Virtual Address Descriptor (`VAD`) extractors rather than file-cache extractors, since decrypted pages live in private memory.
* Check per-section page residency after OEP (`280`): bulk-decrypted modules (`800 -> 830`) have all executable pages populated immediately, whereas page-encrypted modules (`640 -> 840`) leave untouched pages `PAGE_NOACCESS` until faulted in.
* Schedule in-process helpers after the `A07` foreign-thread sweep, and diff two post-boot snapshots taken seconds apart to detect newly faulted pages or active `scribble` re-masking.
{% endstep %}

{% step %}
## Validate reconstructed PE images statically

Verify five structural invariants before trusting a recovered PE:

1. Valid `MZ` and `PE\0\0` signatures, optional-header magic `0x10B` or `0x20B`, and in-bounds section headers.
2. For native modules with a nonzero entry point, `AddressOfEntryPoint` maps into a nonzero executable range (and CRT entry-stub `call`/`jmp` targets stay inside `.text`).
3. Across up to 256 `IMAGE_IMPORT_DESCRIPTOR`s (on native modules), module names decode to printable ASCII `.dll` / `.exe` names and by-name `IMAGE_IMPORT_BY_NAME` strings are readable ASCII.
4. For managed assemblies (`DD[14]` nonzero), `COR20` header `cb == 0x48` and the referenced metadata root begins with `BSJB`.
5. For all DLLs, `DataDirectory[5]` (`BaseReloc`) is nonzero and `DYNAMIC_BASE` (`0x0040`) is set.
{% endstep %}
{% endstepper %}
