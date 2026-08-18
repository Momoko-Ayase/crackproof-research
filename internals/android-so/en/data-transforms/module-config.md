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

The schedule is recognized by a unique four-byte marker `00 01 0e 00` (little-endian bits `0x0100`, round count 14). The following 15 × 16 bytes are the expanded AES-256 decryption round keys, stored with each word byte-reversed. The 32-byte cipher key is recovered from the last two round keys: the final round key concatenated with MixColumns of the previous one. A second copy of the same marker, a truncated schedule, or a round count other than 14 is a format error.

The skip flag lives a fixed distance past the marker in the interpreter-side `0x9B` image. The embedded decoder that ships inside the stage 2 image ends before that flag, so it is definitionally false for that layout. The embedded decoder uses the header seed when a container seed is not present. This fallback is part of the observed layout; it is not a license to guess a seed from plaintext.
