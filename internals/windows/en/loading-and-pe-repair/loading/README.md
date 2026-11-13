---
description: "How self-decrypting loader stages, layout variants, and trial validation recover protected Windows sections."
icon: stairs
---

# Loading and section recovery

Protected Windows containers chain five to eight self-decrypting loader stages whose keys depend on upstream CRC-32 checksums, triangular key schedules, and per-build bytecode stubs before revealing the final section-recovery tables.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-link"></i></td><td><strong>Stage chain and marker layout</strong></td><td>Composite stage decryption and the nine-phase 64-bit marker-layout recovery pipeline.</td><td><a href="stage-chain.md">Stage chain and marker layout</a></td></tr><tr><td><i class="fa-code-branch"></i></td><td><strong>PE32, DLL, and marker-less layouts</strong></td><td>Standard and compact PE32 shells, dedicated 64-bit DLL fixed tables, and marker-less 64-bit discovery.</td><td><a href="layout-variants.md">PE32, DLL, and marker-less layouts</a></td></tr><tr><td><i class="fa-magnifying-glass"></i></td><td><strong>Structural discovery and validation</strong></td><td>Trial decryption, compressed-block verification, and <code>.text</code> page-scramble selection rules.</td><td><a href="discovery-validation.md">Structural discovery and validation</a></td></tr></tbody></table>
