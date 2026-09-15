---
description: "Validate the rebuilt ELF image, program layout, and removal of protection-only data."
---

# ELF output

The final image is rebuilt from the recovered ranges and the original program-header relationships. The output checks include:

* ELF64, little-endian AArch64 identification;
* program-header and section-header ranges inside the file;
* `PT_LOAD` alignment, file size, and memory size relationships;
* dynamic-section pointers into the restored tables;
* relocation entry size and count; and
* an entry-point field cleared to zero — a leftover protector entry means the restoration failed.

The private protection section — always the last section header — is omitted from the output, and the entry-point field is cleared rather than replaced: there is no recovered native ELF entry, because native constructors run from `.init_array`. On compact layouts the program-header table gains one extra read-only `PT_LOAD` for the rebuilt dynamic tables (see [Dynamic linking](dynamic-linking.md)). Protection-only padding is not copied into a loadable segment merely because it fills a file gap.

The output is parsed again from disk. A successful in-memory reconstruction that fails this second parse is treated as a failed restoration.
