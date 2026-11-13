---
description: "Content-based KONN detection, native vs managed PE32/PE32+ classification, and observed layout families."
icon: fingerprint
---

# Recognition and build families

## Content-based recognition and classification

A file matches the outer container signature when:

1. File length is at least `4128` bytes (`0x1020`) and `e_lfanew` (`u32@0x3C`) points to a valid `PE\0\0` signature.
2. `header_kdf` at offset `4096` produces `info[1] == 0x4E4E4F4B` (`KONN`).

Passing both checks identifies a candidate container; full validation requires in-range `info` slices, valid stage descriptors, and passing stage checksums or trial decompression.

Once recognized, standard PE header fields classify the target into four module kinds:

* `IMAGE_FILE_HEADER.Characteristics & 0x2000` (`IMAGE_FILE_DLL`) separates DLLs from EXEs.
* Data directory `14` (`IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR`, starting at optional-header `+96` on PE32 or `+112` on PE32+) separates managed (.NET) assemblies from native binaries.

| `IMAGE_FILE_DLL` | CLR RVA (`DD[14]`) | Module kind |
| --- | --- | --- |
| `0` | `0` | `native-exe` |
| `0` | nonzero | `managed-exe` |
| nonzero | `0` | `native-dll` |
| nonzero | nonzero | `managed-dll` |

Managed EXEs use the same EXE-style container as native EXEs.

```python
MAGIC_KONN = 0x4E4E4F4B  # the shell stamp

def detect(file_data):
    """Return ("native-exe" | "managed-exe" | "native-dll" | "managed-dll",
    magic) for a protected file, or None when the file is not protected by
    this scheme."""
    if len(file_data) < 4128:
        return None
    pe_off = get_u32(file_data, 0x3C)
    if file_data[pe_off:pe_off + 4] != b"PE\0\0":
        return None
    info = header_kdf(file_data)
    if info[1] != MAGIC_KONN:
        return None

    characteristics = get_u16(file_data, pe_off + 4 + 18)   # IMAGE_FILE_HEADER
    is_dll = bool(characteristics & 0x2000)                 # IMAGE_FILE_DLL

    # COM descriptor (CLR) data directory: managed vs native, EXE and DLL alike.
    # Data directories start at optional-header +96 on PE32, +112 on PE32+.
    opt_magic = get_u16(file_data, pe_off + 24)             # 0x10B / 0x20B
    dd_base = 112 if opt_magic == 0x20B else 96
    clr_rva = get_u32(file_data, pe_off + 24 + dd_base + 14 * 8)
    managed = bool(clr_rva)

    if is_dll:
        return ("managed-dll" if managed else "native-dll", info[1])
    return ("managed-exe" if managed else "native-exe", info[1])
```

{% hint style="info" %}
Always read the optional-header magic (`0x10B` vs `0x20B`) before indexing data directories: `DD[14]` sits at `pe + 0xE8` on PE32 and `pe + 0xF8` on PE32+. Reading the wrong offset can misclassify a 32-bit native binary as managed.
{% endhint %}

## Observed layout dimensions

Protected Windows files vary across four structural dimensions (only certain combinations occur: the dedicated DLL container is 64-bit marker-only, and external companions use PE32+ EXE-style shells):

* **Bitness:** PE32+ (`0x20B`, 64-bit) and PE32 (`0x10B`, 32-bit) share `header_kdf` and the core ciphers, while using distinct configuration tables, stage counts, and import/header reconstruction rules (including standard and compact PE32 shell variants).
* **Module kind:** `native-exe`, `managed-exe`, `native-dll`, and `managed-dll`. Even when a managed build leaves the `COR20` header and `BSJB` metadata root readable on disk, its IL method bodies live inside encrypted/compressed section payloads.
* **64-bit configuration discovery:**
  * **Marker layout (classic):** Stage 5 contains literal markers `70 6D 00 00 63 6D 00 00` (`"pm\0\0cm\0\0"`) and `00 00 00 40 01 00 00 00` (`0x40000000, 1`), placing descriptor walks at fixed relative offsets.
  * **Marker-less layout (modern):** omits both markers; Stage 5 slots and bytecode stubs are located through LFSR scans, `trial_byte_rotate2` range checks, `fileCS` distance scoring, and trial decompression.
* **DLL container style:**
  * **Dedicated DLL layout:** a 64-bit DLL-only container (`0x20B`) whose configuration table starts at fixed offset `info[6] + 5592` (`0x15D8`).
  * **EXE-style shell:** wraps 32-bit or 64-bit DLLs in the same staged shell used for EXEs, including optional [external-companion (`._`)](companion-layout.md) splitting.
