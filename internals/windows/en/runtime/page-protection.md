---
description: "On-demand page decryption, loader-code variation, decoys, and self-loading behavior."
---

# Page protection and loader code

## Page-level encryption

The strongest runtime layer is optional and per-module. When enabled (`640` then `840`):

1. Executable sections are bulk-decrypted (status `640`).
2. They are then **re-encrypted page by page**, and every page is set to `PAGE_NOACCESS` (status `840`).
3. Execution that reaches a protected page faults; an exception handler decrypts the page on demand and resumes execution.

The exception handling is installed by **patching `ntdll!KiUserExceptionDispatcher`** to jump into the protector's handler, which chains back to normal SEH when it is done. The kernel delivers every usermode exception to this single entry point, so the handler runs ahead of all SEH registrations — and is invisible to tools that walk the SEH chain looking for hooks.

A consequence for memory analysis: a naive dump of a page-encrypted module captures only the pages touched since startup (the demand-decrypted working set); the rest is ciphertext or `PAGE_NOACCESS` filler. A complete image requires forcing every page to fault in first. Some builds additionally **scribble**: selected bytes of each decrypted page are XORed with random values once the page is resident, so a raw dump needs de-scribbling. The scribble is a per-build option and not always present — some page-encrypted modules dump cleanly once every page has been touched.

The page-fault handler does not live inside the protected module's image. It ships in a manually mapped support module (`HtdpStub2.dll` — see [Htsysm kernel components](kernel-components.md)), which is why handler signatures are absent when only the main module is dumped.

## The loader's own code: polymorphism and decoys

The loader defends its code as aggressively as its data. Techniques observed in the final stage (stage 5) and its bootstrap:

**Polymorphic emit.** The same algorithm appears as many permuted copies — one observed image carries 16 instances of one cipher prologue, differing only in cosmetic junk-jump placement. Disassemblers see 16 unrelated functions; the semantics are identical.

**Anti-disassembly.** Junk bytes after unconditional jumps, jumps into the middle of multi-byte instructions, and return-address arithmetic (for example `call $+5` followed by add/sub of two constants whose difference is the distance to the real continuation, the modified return address then being discarded). Linear and even recursive-descent disassembly desynchronize; one 12.9 KB stage-5 blob decompiles almost entirely to "control flows out of bounds".

**No-op decoy stubs.** The natural entry points are traps for the analyst's patience, not real code. One stub saves all 16 GPRs, performs the VMware backdoor probe, compares the result, and then executes `jne $+2` with a displacement of 0 — both branches reach the same instruction — restores every register, and returns. Its only side effect is the **timing** of the `in` instruction, consumed elsewhere. Another decoy hides its payload behind a trap flag: `pushfq; or [rsp], 0x100; popfq` raises `#DB`; under normal execution an SEH redirect skips the code after it, and only if a debugger (or naive emulator) swallows the exception and continues does the "hidden" path run — a path that goes nowhere useful.

**Self-modifying metadata.** Stage tables are zeroed after use: markers present in the pre-load image are overwritten by the time the module finishes initializing, so a post-boot dump is missing structures the static file contains.

## Self-loading from disk

The final stage does not do reflective in-memory loading. Its API string table contains `GetModuleFileNameW/A`, `CreateFileW`, `CreateFileMappingA`, `MapViewOfFile`, `UnmapViewOfFile`, `GetFileSize`, `GetFullPathNameW/A`, `CloseHandle`, `RtlGetVersion`, `SystemTimeToFileTime`, `Sleep` — file I/O and module-path APIs, with no allocation, protection, or loader APIs. The stage resolves its own on-disk path, maps the protected file as a memory view, and reads the encrypted payload from that view. (This is also why a static analysis can hand the same algorithm the raw file bytes and replay it offline.)

Runtime state is held in a context structure addressed through a reserved register: function pointers at fixed slots, a doubly indirect pointer to the image buffer, and a per-slot table built by an unrolled `lea`-and-store sequence. API addresses are read from the module's own OS-resolved import table — no PEB walk appears anywhere in the stage, so the module relies on the ordinary Windows loader having bound its imports, even though its stored `AddressOfEntryPoint` is junk and the OS never calls its real entry.

The same stage contains its own `.reloc` walker: relocations are applied by the loader (status `655`), not the OS, consistent with the `/FIXED` handling in [PE transformations](../pe-reconstruction/README.md).

