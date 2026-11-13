---
description: "Rebuild PE section headers, entry points, data directories, imports, TLS, exports, relocations, and CLR tables."
icon: puzzle-piece
---

# PE reconstruction

Section recovery yields an RVA-indexed memory buffer (`SizeOfImage` bytes). Turning that buffer back into a valid, loadable PE file requires restoring cleared or redirected header fields, imports, TLS state, exports, base relocations, `.text` page scrambles, and CLR metadata for the build's layout family.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-memory"></i></td><td><strong>Headers, sections, and zero-fill ranges</strong></td><td>RVA-mapped section headers, 32-bit file compaction, transient EP/directory blocks, and <code>.bss</code> zero-fill chains.</td><td><a href="memory-image.md">Headers, sections, and zero-fill ranges</a></td></tr><tr><td><i class="fa-sitemap"></i></td><td><strong>Imports, TLS, and exports</strong></td><td>Family-specific import recovery, <code>.kmiat</code> rebuilding, TLS restoration and relocation re-arming, and stub exports.</td><td><a href="imports-tls-exports.md">Imports, TLS, and exports</a></td></tr><tr><td><i class="fa-cubes"></i></td><td><strong>Relocations, page transforms, and CLR data</strong></td><td><code>/FIXED</code> vs ASLR relocation policies, <code>.text</code> scramble ordering, and surgical CLR metadata restoration.</td><td><a href="relocations-managed.md">Relocations, page transforms, and CLR data</a></td></tr></tbody></table>
