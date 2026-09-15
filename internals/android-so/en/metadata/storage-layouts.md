---
description: "Distinguish external, embedded, and XOR-wrapped IL2CPP metadata without changing its logical format."
---

# Storage layouts

Deployments use three storage variants:

| Variant | Where the bytes are found | Recognition |
| --- | --- | --- |
| External | A separate metadata file loaded by the runtime | File begins with the IL2CPP magic and a valid version/table layout |
| Embedded | A protected record inside the native-library container | Record decodes to the same magic, version, and table relationships |
| Embedded slim + XOR | A blob inside the restored image, wrapped in a per-word XOR layer | After the XOR is removed, a version-24 header under the same magic |

The first two variants change how bytes are located, not how the metadata tables are interpreted. The source location stays with the record, and the same byte range checks apply either way. A file that has the magic but not coherent offsets isn't accepted.

The third variant is the only one whose keys aren't in the file. Observed shape: a 0x100-byte header followed by a fixed number of segments (256), with one u32 key per header word and per segment and irregular segment boundaries.

Those keys are generated inside the metadata-source subsystem at runtime. Derivation of the keystream from the protected image alone is untraced. Later builds in the same family ship external plaintext metadata instead.

The unwrapped blob stores its patched sanity and version fields byte-swapped. Rewritten to the standard magic and version 24, it's a well-formed metadata file, but its records are the older layout, not the version 29/31/39 MethodDef tables.
