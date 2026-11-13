---
description: "Fail-closed validation checklist and observed Android SO format constants."
icon: compass
---

# Analysis

ELF recognition, Stage 1 and Stage 2 decryption, dynamic-table reconstruction, and IL2CPP metadata restoration each validate structural bounds before proceeding to the next stage.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-check"></i></td><td><strong>Validation checklist</strong></td><td>Ordered fail-closed checks across recognition, stream extraction, ELF reconstruction, and metadata.</td><td><a href="validation.md">Validation checklist</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>Constants</strong></td><td>Summary table of observed magic values, offsets, cipher constants, and module IDs.</td><td><a href="constants.md">Constants</a></td></tr></tbody></table>
