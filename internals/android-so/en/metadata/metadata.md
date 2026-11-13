---
description: "IL2CPP metadata method-token and methodIndex permutations (v24.1, v29, v31, v39) and storage variants on Android."
icon: database
---

# Metadata

On Unity IL2CPP Android builds, CrackProof protects `global-metadata.dat` alongside `libil2cpp.so`. Depending on the metadata version and packaging style, it either permutes method tokens or `methodIndex` fields inside an external `global-metadata.dat` file (restored at runtime by module `0x0C`'s `mmap` hook) or wraps a slim version-24 metadata blob inside the `.so` data section with 32-bit XOR keys.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-hashtag"></i></td><td><strong>Method tokens</strong></td><td>Five-round inverse permutation across versions 29, 31, and 39, structural v31 fallback, and version 24.1 <code>methodIndex</code> restoration.</td><td><a href="method-tokens.md">Method tokens</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>Storage layouts</strong></td><td>External <code>global-metadata.dat</code> pairing rules vs embedded XOR-wrapped slim v24 metadata blobs.</td><td><a href="storage-layouts.md">Storage layouts</a></td></tr></tbody></table>
