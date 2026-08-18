---
description: "ELF properties and private-section facts used to identify protected Android libraries."
---

# Protected ELF

## Required ELF shape

Recognition accepts ELF64, little-endian files for AArch64. The file must contain the dynamic-linking information expected by a native shared library:

| Section | Why it matters |
| --- | --- |
| `.dynsym` and `.dynstr` | Dynamic symbols and their names |
| `.gnu.hash` | GNU symbol lookup data |
| `.gnu.version` | Symbol-version indexes |
| `.gnu.version_r` | Required version definitions |
| One `SHT_LOUSER` section | Private protection payload |

The private section is the distinguishing feature. More than one private section, a section whose file range is outside the file, or an ELF class/endianness mismatch is rejected before any decryption is attempted.

`.init_array[0]` points at the stage 1 stub in the intact `.text` head. Later entries point into ranges that are hollow on disk and only become valid after restoration.

## What remains visible

The protected file still has a usable ELF header, program headers, section headers, and dynamic section. Their values may describe the protected layout rather than the final in-memory image, so they are treated as input to recovery, not as proof that the output is already correct.

The private section's name is not used as the only recognition signal. Section type, range, header fields, and the stream checks described on the next pages must agree.
