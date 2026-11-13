---
description: "Load-time execution from the Stage 1 .init_array stub through nested Stage 2 interpreters and environment probes."
icon: play
---

# Runtime

At load time, the Android dynamic linker maps the hollowed ELF and runs `.init_array`, entering the Stage 1 bootstrap stub. Stage 1 maps and decrypts Stage 2 (`0xE2`), which allocates a 256-slot module table, walks nested interpreter streams (`0xE2`..`0xE8`), runs usermode environment and integrity probes, restores the in-memory ELF segments and relocations, and dispatches the original constructors through module `0x98`.

Static restoration needs only the container, symbol, relocation, constructor, and metadata artifacts (`0x9B`, `0x9D`, `0x9E`, plus optional `0x96`, `0x98`, and `0x0C`); the environment-check modules execute only at runtime.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-bolt"></i></td><td><strong>Stage 1 bootstrap</strong></td><td>Self-discovery through <code>/proc/self/maps</code>, <code>SHT_LOUSER</code> decryption, page-size probing, and register handoff.</td><td><a href="stage1-bootstrap.md">Stage 1 bootstrap</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>Stage 2 interpreter</strong></td><td>The 256-slot module table, <code>0x5C</code> record descriptors, and layered <code>0xE2</code>..<code>0xE8</code> stream execution.</td><td><a href="stage2-interpreter.md">Stage 2 interpreter</a></td></tr><tr><td><i class="fa-user-shield"></i></td><td><strong>Environment and integrity checks</strong></td><td>Native-bridge detection, <code>PTRACE_SEIZE</code> helper process, <code>/proc/&lt;pid&gt;/mem</code> traps, and APK signature checks.</td><td><a href="environment-checks.md">Environment and integrity checks</a></td></tr><tr><td><i class="fa-layer-group"></i></td><td><strong>Runtime modules</strong></td><td>Catalog of observed Stage 2 module identifiers across interpreters, restoration, and environment probes.</td><td><a href="modules.md">Runtime modules</a></td></tr></tbody></table>
