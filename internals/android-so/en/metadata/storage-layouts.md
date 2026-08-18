---
description: "Distinguish external, embedded, and XOR-wrapped IL2CPP metadata without changing its logical format."
---

# Storage layouts

Deployments use three storage variants:

| Variant | Where the bytes are found | Recognition |
| --- | --- | --- |
| External | A separate metadata file loaded by the runtime | File begins with the IL2CPP magic and a valid version/table layout |
| Embedded | A protected record inside the native-library container | Record decodes to the same magic, version, and table relationships |
| Embedded slim + XOR | A blob inside the restored image, wrapped in a per-word XOR layer | After the XOR is removed, the same magic, version, and table relationships |

The storage location changes how bytes are located, not how the metadata tables are interpreted. The extractor keeps the source location in its record, then passes the byte range to the same metadata validator. A candidate that has the magic but not coherent offsets is not accepted.

The third variant is the only one whose keys are not in the file. Observed shape: a 0x100-byte header followed by a fixed number of segments (256), with one u32 key per header word and per segment and irregular segment boundaries. Those keys are generated inside the metadata-source subsystem at runtime. Derivation of the keystream from the protected image alone is untraced; later builds in the same family simply ship external plaintext metadata instead.
