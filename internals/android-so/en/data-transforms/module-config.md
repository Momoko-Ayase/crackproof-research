---
description: "Fields supplied by the configuration module to later stream decoders."
---

# Module configuration

The configuration record is supplied by module `0x9B`. It provides the seeds and AES material needed by the container and symbol modules.

| Value | Use |
| --- | --- |
| Header seed | Fallback seed for decoding the outer container header |
| Container seed | Seed for the container's rolling transform |
| AES-256 key or expanded schedule | Optional block-cipher layer |
| AES skip flag | Indicates that the AES layer is absent for this build |

The expanded AES schedule is either absent or has the size expected for AES-256. A malformed schedule, an unsupported key size, or a skip flag that contradicts the record length causes the module to fail.

The embedded decoder uses the header seed when a container seed is not present. This fallback is part of the observed layout; it is not a license to guess a seed from plaintext.
