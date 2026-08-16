---
description: "Decode container descriptors, segment transforms, and raw or compressed writes."
---

# Container transforms

Module `0x9D` describes a container with a `0x5c`-byte protected descriptor, a container header, a tree of records, and segment data. The descriptor gives the offsets and sizes needed to bound every later read.

## Segment processing

Each segment has a target image range and a source range. The segment transform uses the seeds from module `0x9B`; an optional AES layer is applied when the configuration does not request a skip. The decoder writes only to the declared target range.

The writer stream starts with a 16-byte header. A write is either raw data or a compressed block. For either form, the decoder requires:

1. source and target ranges inside the containing record;
2. exact source consumption; and
3. exact target length.

The tree may contain empty segments or metadata-only records. They are retained as records but do not create executable bytes. Overlap with a previously materialized range is rejected unless the record explicitly describes the same range and content.
