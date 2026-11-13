---
description: "GF(2^32) arithmetic, module seeds, AES schedules, container decoders, and Huffman/LZ compression in Android streams."
icon: shuffle
---

# Data transforms

Decryption proceeds through four layers: a 32-bit word cipher in Stage 1, GF(2³²)-mixed stream headers and descriptors in Stage 2, per-segment rolling word ciphers with optional AES-256-CBC decryption in containers, and Huffman/LZ decompression.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-rotate"></i></td><td><strong>Word, stream, and record ciphers</strong></td><td>GF(2³²) fixed multiplication, Stage 1 word cipher, stream headers, <code>0x5C</code> record descriptors, and the <code>0x9D</code> descriptor.</td><td><a href="word-and-record.md">Word, stream, and record ciphers</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>Module configuration</strong></td><td>Schedule marker <code>00 01 0e 00</code>, AES-256 key recovery, and seed layout in module <code>0x9B</code> vs embedded Stage 2.</td><td><a href="module-config.md">Module configuration</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>Container transforms</strong></td><td>Container headers, segment rolling cipher, file-layout writers, and the auxiliary ELF relocation container.</td><td><a href="container.md">Container transforms</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>Huffman and LZ compression</strong></td><td>3-byte Huffman forest, 16-bit prefix table, four token modes, and exact bit/byte consumption checks.</td><td><a href="compression.md">Huffman and LZ compression</a></td></tr></tbody></table>
