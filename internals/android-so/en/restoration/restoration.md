---
description: "Extract Stage 2 module artifacts, reconstruct dynamic-linking tables, and emit a clean ELF64 shared library."
icon: puzzle-piece
---

# Restoration

Static restoration proceeds in two stages: extracting the Stage 2 module set from `SHT_LOUSER`, then rebuilding the ELF load segments, dynamic-linking tables, and section headers before verifying the output.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-route"></i></td><td><strong>Module streams</strong></td><td>Required baseline modules (<code>0x9B</code>, <code>0x9D</code>, <code>0x9E</code>) and optional static modules (<code>0x96</code>, <code>0x98</code>, <code>0x0C</code>).</td><td><a href="module-streams.md">Module streams</a></td></tr><tr><td><i class="fa-link"></i></td><td><strong>Dynamic linking</strong></td><td>Hidden symbols, <code>0x96</code> symbol unpermutation, omitted <code>libc</code> PLT slots, constructor recovery, and <code>PT_LOAD</code> placement.</td><td><a href="dynamic-linking.md">Dynamic linking</a></td></tr><tr><td><i class="fa-file-export"></i></td><td><strong>ELF output</strong></td><td>Stripping <code>SHT_LOUSER</code>, clearing <code>e_entry</code>, relocating non-alloc sections, and hard vs diagnostic checks.</td><td><a href="elf-output.md">ELF output</a></td></tr></tbody></table>
