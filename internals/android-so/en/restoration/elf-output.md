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
* an entry point inside an executable mapped range.

After those checks, the private protection section is removed or neutralized, and the protected entrypoint is replaced with the recovered native entry. Protection-only padding is not copied into a loadable segment merely because it fills a file gap.

The output is parsed again from disk. A successful in-memory reconstruction that fails this second parse is treated as a failed restoration.
