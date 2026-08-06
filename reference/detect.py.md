---
description: >-
  Content-based detection and classification of protected files (KONN magic,
  EXE/DLL, managed/native).
---

# detect.py

The detection and classification logic documented in [The protected file format](https://launchcore.gitbook.io/crackproof-research/docs/file-format#recognition-and-classification).

```python
"""Content-based detection and classification of a protected PE file.

A protected file is recognized by content, never by name or extension:
derive the 8-dword info table from offset 4096 and check the magic in
info[1]. The PE header stays plaintext, so the usual PE fields classify
the file further.
"""

MAGIC_KONN = 0x4E4E4F4B  # the shell stamp


def get_u16(d, off):
    return d[off] | (d[off + 1] << 8)


def get_u32(d, off):
    return d[off] | (d[off + 1] << 8) | (d[off + 2] << 16) | (d[off + 3] << 24)


def header_kdf(file_data, offset=4096):
    info = [0] * 8
    info[0] = get_u32(file_data, offset)
    k = info[0]
    for i in range(7):
        cell = get_u32(file_data, offset + 4 + 4 * i)
        info[i + 1] = k ^ cell
        k = (i * i) ^ ((k + cell - i) & 0xFFFFFFFF)
    return info


def detect(file_data):
    """Return ("exe" | "native-dll" | "managed-dll", magic) for a protected
    file, or None when the file is not protected by this scheme."""
    if len(file_data) < 4128:
        return None
    pe_off = get_u32(file_data, 0x3C)
    if file_data[pe_off:pe_off + 4] != b"PE\0\0":
        return None
    info = header_kdf(file_data)
    if info[1] != MAGIC_KONN:
        return None

    # IMAGE_FILE_HEADER.Characteristics, IMAGE_FILE_DLL bit
    characteristics = get_u16(file_data, pe_off + 4 + 18)
    if not characteristics & 0x2000:
        return ("exe", info[1])

    # DLL: the COM descriptor (CLR) data directory decides managed vs native.
    # Data directories start at optional-header +96 on PE32, +112 on PE32+.
    opt_magic = get_u16(file_data, pe_off + 24)
    dd_base = 112 if opt_magic == 0x20B else 96
    clr_rva = get_u32(file_data, pe_off + 24 + dd_base + 14 * 8)
    return ("managed-dll" if clr_rva else "native-dll", info[1])
```
