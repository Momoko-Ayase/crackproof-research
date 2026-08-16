---
description: "The reversible data transforms used across Windows headers, loader stages, names, sections, and code pages."
---

# Data transforms

CrackProof layers several small transforms rather than relying on one container-wide cipher. Their inputs, address dependence, and order matter: applying the correct transform to the wrong range can still produce plausible bytes.

The pages separate the transforms by role:

- [Rolling-key and rotation ciphers](rolling-and-rotation.md) cover the early stage and small-record operations.
- [LFSR, string, and page transforms](lfsr-strings-pages.md) cover embedded instruction streams, import names, and sparse code-page changes.
- [Checksums and key progression](checksums.md) explain record validation and how one result advances the next key.
- [AES-CBC](aes.md), [Huffman/LZ compression](compression.md), and the [per-build byte transform](bytecode-transform.md) form the main section-data path.
