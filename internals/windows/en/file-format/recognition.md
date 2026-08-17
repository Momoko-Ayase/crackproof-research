---
description: "Structural checks that distinguish protected PE files and the layouts observed across build families."
---

# Recognition and build families

## Recognition and classification

A protected file is recognized by content, never by name or extension. The initial filter is:

1. It is at least 4128 bytes long and has a valid `PE\0\0` signature at `e_lfanew` (`u32@0x3C`).
2. The KDF over offset 4096 yields `info[1] == KONN`.

These two checks identify a candidate. Before accepting its layout, every `info` range must also fit the file, stage and section records must have valid bounds, and at least one downstream checksum or decode must succeed. `KONN` alone is not enough to trust all derived offsets.

Classification then uses ordinary PE fields. Both fields apply to every candidate; EXE versus DLL and native versus managed are independent:

- `IMAGE_FILE_HEADER.Characteristics & 0x2000` (`IMAGE_FILE_DLL`) distinguishes DLL from EXE.
- The COM descriptor (CLR) data directory — entry 14, at optional-header `+96` on PE32 or `+112` on PE32+ — distinguishes managed (.NET) from native.

The four combinations are:

| `IMAGE_FILE_DLL` | CLR RVA | Kind |
| --- | --- | --- |
| clear | 0 | native EXE |
| clear | nonzero | managed EXE |
| set | 0 | native DLL |
| set | nonzero | managed DLL |

A managed EXE uses the same EXE-style container as a native EXE. The CLR directory is the only PE-header difference that classification needs. It is not a fifth layout family.

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
Using the wrong data-directory base (96 vs 112) reads the wrong dword and can misclassify a 32-bit native image as managed. The optional-header magic must be read first. Skipping the CLR check on EXEs folds managed EXEs into native EXEs.
{% endhint %}

## Build families

Protected files observed in the wild vary along four axes. The axes are independent; every combination needs handling.

**Bitness.** PE32+ (optional-header magic `0x20B`, 64-bit) and PE32 (`0x10B`, 32-bit) containers share the header/payload layer but use entirely different configuration layouts, stage structures, and final PE fixups.

**Object kind.** Native EXE, managed EXE, native DLL, and managed DLL (see classification above). Some managed layouts preserve the COR20 header and BSJB metadata stream verbatim in the protected file. This does not make the managed method bodies plaintext; they still belong to sections handled by the normal recovery path.

**Configuration layout.** Two generations of the 64-bit loader configuration:

- The **marker layout** (older builds) embeds the byte markers `70 6D 00 00 63 6D 00 00` (`"pm\0\0cm\0\0"` — the loader's two-letter submodule codes) and `00 00 00 40 01 00 00 00` (a `0x40000000, 1` dword pair) in the final loader stage. Every important table is at a fixed offset from these markers.
- The **marker-less layout** (newer builds, including EXE-style shells wrapped around DLLs) omits both markers. Tables are found from their record shape, embedded transform programs, pointer ranges, and a trial decode of a compressed record.

**DLL packaging.** Two ways DLLs are protected:

- The **dedicated DLL layout** (older): a DLL-specific container whose configuration block sits at a fixed offset (`keys[6] + 5592`) rather than a scanned anchor.
- The **EXE-style shell** (newer): DLLs are wrapped in the same shell layout as EXEs. The external-companion split below is an instance of this family.
