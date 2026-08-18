---
description: "Stage 1 bootstrap, the stage 2 interpreter, and runtime module roles."
---

# Runtime

Static restoration reconstructs an ELF image from the private section. The pages in this group describe what the same records do when the library loads: how stage 1 finds itself, how stage 2 interprets nested streams, and what the materialized modules check or restore.

Restoration still needs only modules `0x9B`, `0x9D`, and `0x9E`. The other identifiers are runtime objects. Their absence from a restored image is not a restoration failure.

| Page | What it covers |
| --- | --- |
| [Stage 1 bootstrap](stage1-bootstrap.md) | `/proc/self/maps`, the `SHT_LOUSER` section, and the jump into stage 2 |
| [Stage 2 interpreter](stage2-interpreter.md) | The module table, record streams, and nested interpreters `0xE2`–`0xE8` |
| [Environment and integrity checks](environment-checks.md) | Translation-layer, ptrace, package, and memory-visibility probes |
| [Runtime modules](modules.md) | Observed roles of command identifiers after they are materialized |
