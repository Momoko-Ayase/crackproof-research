---
description: "How encrypted loader stages are found, decoded, and used to recover protected Windows sections."
---

# Loading and section recovery

The bootstrap does not expose one stable table at a fixed offset. It decrypts several stages, and later stages contain the records and transform programs required to recover the original sections.

- [Stage chain and marker layout](stage-chain.md) follows the common 64-bit sequence.
- [PE32, DLL, and marker-less layouts](layout-variants.md) records the main structural differences.
- [Structural discovery and validation](discovery-validation.md) explains how candidates are selected when fixed markers are absent and how a trial decode rejects false matches.
