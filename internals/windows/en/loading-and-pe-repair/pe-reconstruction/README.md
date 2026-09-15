---
description: "How a recovered memory image is turned back into a coherent PE file."
---

# PE reconstruction

Section recovery produces an RVA-oriented memory image. A usable PE file also needs coherent headers, file offsets, data directories, imports, TLS state, exports, relocations, and, for managed images, CLR structures.

- [Headers, sections, and zero-fill ranges](memory-image.md)
- [Imports, TLS, and exports](imports-tls-exports.md)
- [Relocations, page transforms, and CLR data](relocations-managed.md)

These steps are layout-sensitive. In particular, old fixed-base executables, rebased DLLs, external-companion images, and CLR images can't share one blanket directory policy.
