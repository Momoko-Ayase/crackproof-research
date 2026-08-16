---
description: "Distinguish external and embedded IL2CPP metadata without changing its logical format."
---

# Storage layouts

Deployments use two storage variants:

| Variant | Where the bytes are found | Recognition |
| --- | --- | --- |
| External | A separate metadata file loaded by the runtime | File begins with the IL2CPP magic and a valid version/table layout |
| Embedded | A protected record inside the native-library container | Record decodes to the same magic, version, and table relationships |

The storage location changes how bytes are located, not how the metadata tables are interpreted. The extractor keeps the source location in its record, then passes the byte range to the same metadata validator. A candidate that has the magic but not coherent offsets is not accepted.
