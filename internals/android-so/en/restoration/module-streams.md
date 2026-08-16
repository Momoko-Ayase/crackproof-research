---
description: "Dispatch nested records and apply the required Android decoder modules."
---

# Module streams

The initial stream identifier is `0xE2`. The required module set for ELF restoration is:

| Module | Role |
| --- | --- |
| `0x9B` | Seeds, AES material, and configuration |
| `0x9D` | Protected descriptors, segments, and writer streams |
| `0x9E` | Hidden dynamic-symbol patches |

Direct records derive a child identifier from their command identifier. The dispatcher keeps a module registry and passes each record only to the module that declares that identifier. It records the content hash of each accepted child, so the same stream cannot silently overwrite a previously restored range.

An unknown module, a missing required module, or a child whose declared range falls outside its parent stops restoration. The partial image is not published as a successful result.
