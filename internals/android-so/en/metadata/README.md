---
description: "IL2CPP metadata signatures, method-token ranges, and storage variants."
---

# Metadata

Some Android builds protect IL2CPP metadata alongside native image ranges. The metadata rules are independent of ELF dynamic linking, so they are kept in their own group. Storage may be an external file, an embedded record, or an XOR-wrapped slim blob inside the restored image; the table layout is the same in each case.
