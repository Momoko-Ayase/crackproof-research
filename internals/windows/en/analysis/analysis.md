---
description: "Practical analysis workflow, architectural limitations, -GMD IL2CPP metadata remapping, and constant tables."
icon: compass
---

# Analysis notes

Static and runtime analysis of CrackProof-protected Windows binaries relies on structural cross-checks, mapping debug-log codes to stage routines, and format-specific post-checks.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-check"></i></td><td><strong>Analysis workflow</strong></td><td>Step-by-step guide to enabling debug logs, locating stages, dumping page-protected modules, and verifying PE outputs.</td><td><a href="workflow.md">Analysis workflow</a></td></tr><tr><td><i class="fa-triangle-exclamation"></i></td><td><strong>Observed limitations</strong></td><td>Reproducible design limitations across VM checks, debug logging, demand paging, drivers, and CRC chains.</td><td><a href="observed-limitations.md">Observed limitations</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>il2cpp metadata obfuscation</strong></td><td>Reversing the keyless Windows <code>-GMD</code> sparse MethodDef token remap on Unity IL2CPP builds.</td><td><a href="il2cpp-metadata.md">il2cpp metadata obfuscation</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>Constants and offsets</strong></td><td>Master reference tables for magics, container formulas, PE32/PE32+ field offsets, and bytecode opcodes.</td><td><a href="constants.md">Constants and offsets</a></td></tr></tbody></table>
