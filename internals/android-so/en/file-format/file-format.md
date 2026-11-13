---
description: "Recognize a protected Android ELF64 library and trace its Stage 1 and Stage 2 payload boundaries."
icon: folder-tree
---

# File format

A protected Android shared library remains a valid little-endian ELF64 AArch64 binary. Its dynamic-linking sections stay visible in the section header table, while its loadable code and data ranges are hollowed out and moved into a single trailing `SHT_LOUSER` section.

Format validation is strict: header types, section offsets, parameter bounds, and nested stream ranges must all pass before a file is accepted. Load-time discovery of the same structures is covered in [Stage 1 bootstrap](../runtime/stage1-bootstrap.md).

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-file-code"></i></td><td><strong>Protected ELF</strong></td><td>Required ELF64 headers, dynamic sections, <code>.init_array</code> bootstrap slot, and companion APK artifacts.</td><td><a href="protected-elf.md">Protected ELF</a></td></tr><tr><td><i class="fa-box-archive"></i></td><td><strong>Stage 1 header</strong></td><td>Layout of the <code>SHT_LOUSER</code> payload section, the 32-byte word header, and relative offset bounds.</td><td><a href="stage1.md">Stage 1 header</a></td></tr><tr><td><i class="fa-bars-staggered"></i></td><td><strong>Stage 2 streams</strong></td><td><code>0x5C</code>-byte record descriptors, direct slices vs child streams, and container payload dispatch.</td><td><a href="stage2-streams.md">Stage 2 streams</a></td></tr></tbody></table>
