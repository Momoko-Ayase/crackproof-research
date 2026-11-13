---
description: "On-disk layout, KONN header recognition, build-family classification, and external companion splits."
icon: folder-tree
---

# Protected file structure

Protected Windows binaries preserve a loadable outer PE header in the first `0x1000` bytes while storing the encrypted parameter header at `0x1000` and the staged loader plus compressed application sections beyond it (or in a sibling `._` companion file).

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-box-archive"></i></td><td><strong>Container and encrypted header</strong></td><td>The fixed <code>0x1000</code> split, the eight-dword <code>info</code> header KDF, and payload transfer ranges.</td><td><a href="container-layout.md">Container and encrypted header</a></td></tr><tr><td><i class="fa-fingerprint"></i></td><td><strong>Recognition and build families</strong></td><td>Content-based <code>KONN</code> detection, PE32 vs PE32+ CLR classification, and layout families.</td><td><a href="recognition.md">Recognition and build families</a></td></tr><tr><td><i class="fa-copy"></i></td><td><strong>Section data and companion files</strong></td><td>Complement-encoded section data base at <code>0x1080</code> and external <code>._</code> companion pairing and overlays.</td><td><a href="companion-layout.md">Section data and companion files</a></td></tr></tbody></table>
