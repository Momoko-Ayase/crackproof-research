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

Section names are read from the ELF string table (`.shstrtab`), which must be a well-formed `SHT_STRTAB`. A malformed string table is a format error, and names are never guessed.

Restoration additionally requires `.dynamic`, `.rela.dyn`, and `.rela.plt`, each exactly once. The private section is the last section header and begins at the 16-byte-aligned end of the file-backed `PT_LOAD` range.

`.init_array[0]` points at the stage 1 stub in the intact `.text` head. Later entries point into ranges that are empty on disk and only become valid after restoration.

## What remains visible

The protected file still has a usable ELF header, program headers, section headers, and dynamic section. Their values may describe the protected layout rather than the final in-memory image, so they're treated as input to recovery, not as proof that the output is already correct.

The private section's name isn't used as the only recognition signal. Section type, range, header fields, and the stream checks described on [Stage 1 header](stage1.md) and [Stage 2 streams](stage2-streams.md) must agree.

The same APK often ships a second native library whose file name is `lib__XXXX__.so`, where `XXXX` is a short build stamp, and a high-entropy `assets/<id>/data1.dat` of about 180 KiB.

Those files are part of the protection, not of the restored ELF. The named library is a second copy of the stage 1/2 stub, and `data1.dat` holds a small record table (library names and per-library configuration). Neither is a substitute for the `SHT_LOUSER` checks in [Required ELF shape](#required-elf-shape).
