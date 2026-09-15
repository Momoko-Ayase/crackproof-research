---
description: "Dispatch nested records and apply the required Android decoder modules."
---

# Module streams

The initial stream identifier is `0xE2`. Stage 2 first registers itself as `0xE2` and the file-tail mapping as `0xD0` in a 256-entry table (`0x1800` bytes, 24 bytes per slot). The required module set for ELF restoration is:

| Module | Role |
| --- | --- |
| `0x9B` | Seeds, AES material, and configuration |
| `0x9D` | Protected descriptors, segments, and compressed-block streams |
| `0x9E` | Hidden dynamic-symbol patches |

Direct records derive a child identifier from their command identifier. The dispatcher keeps a module registry and passes each record only to the module that declares that identifier. It records the content hash of each accepted child, so the same stream can't silently overwrite a previously restored range.

An unknown module, a missing required module, or a child whose declared range falls outside its parent stops restoration. The partial image isn't published as a successful result.
