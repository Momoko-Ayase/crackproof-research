---
description: "Follow the stage 2 record stream and its nested direct records."
---

# Stage 2 streams

Stage 2 begins with stream identifier `0xE2`. Its header is eight bytes, followed by a sequence of fixed-size record descriptors. The observed descriptor size is `0x5c` bytes.

## Record boundaries

Each descriptor carries a command identifier, flags, image and metadata offsets, sizes, a copied identifier, and entry/initialization values. The exact payload starts after the descriptor; every offset and size is checked against the containing stream before the next record is read.

The direct flag has value `2`. A direct record isn't a compressed container: it points to a child stream whose identifier is `command_id - 0x10`. Observed pairs are `0xF3`→`0xE3` through `0xF8`→`0xE8`. The child is interpreted only when the corresponding module definition is available. Flag `0x100` skips that record's init and entry callbacks. A registry keyed by `(stream id, content hash)` prevents the same child from being applied twice.

The runtime walk of these nested streams, including the 256-entry module table, is described in [Stage 2 interpreter](../runtime/stage2-interpreter.md).

## Nested containers

Non-direct records point to a container payload. The container descriptor and its segment records are decoded by the module selected for that record. A record may include both image bytes and metadata bytes; those ranges are kept separate so that metadata isn't copied into an ELF segment.

Truncated descriptors, overlapping ranges, impossible child identifiers, and streams that don't consume their declared payload are rejected. A valid first record isn't enough: the complete sequence must be structurally consistent.
