---
description: "Per-build nine-opcode AL x86 bytecode stubs, 256-byte LUT precomputation, and family-specific stub discovery."
icon: microchip
---

# Per-build byte transform

## Per-build `AL` bytecode permutation

At pack time, CrackProof synthesizes two short per-build x86 functions that accept one byte in `AL`, apply a random chain of arithmetic and bit-rotation instructions, and return (`RET`): one stub decodes the final loader stage, and a second stub decodes every section payload block between AES-CBC decryption and Huffman/LZ decompression.

Each stub occupies a 96-byte slot masked by the [LFSR keystream](lfsr-strings-pages.md#lfsr-keystream-dd6) (program byte length in plaintext at `+95`). Only nine x86 instruction encodings appear:

| Bytes | x86 instruction | Decoded op |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | skipped |
| `C0 C0 ib` (`mod=3, reg=0, rm=0`) | `ROL AL, imm8` | `("rol", imm)` |
| `C0 C8 ib` (`mod=3, reg=1, rm=0`) | `ROR AL, imm8` | `("ror", imm)` |
| `FE C0` (`mod=3, reg=0, rm=0`) | `INC AL` | `("inc",)` |
| `FE C8` (`mod=3, reg=1, rm=0`) | `DEC AL` | `("dec",)` |
| `C3` | `RET` | end of program |

Any other opcode or `ModR/M` byte rejects the candidate slot.

```python
def generate(data, offset=0):
    """Decode the stub at `offset` into an op list, or return None if the
    byte stream is not a valid stub (must terminate in RET)."""
    pos = offset
    ops = []

    def take():
        nonlocal pos
        if pos >= len(data):
            return None
        b = data[pos]
        pos += 1
        return b

    while True:
        op = take()
        if op is None:
            return None
        if op == 0x04:
            imm = take()
            if imm is None:
                return None
            ops.append(("add", imm))
        elif op == 0x2C:
            imm = take()
            if imm is None:
                return None
            ops.append(("sub", imm))
        elif op == 0x34:
            imm = take()
            if imm is None:
                return None
            ops.append(("xor", imm))
        elif op == 0x90:
            pass
        elif op in (0xC0, 0xFE):
            modrm = take()
            if modrm is None:
                return None
            mod, reg, rm = modrm >> 6, (modrm >> 3) & 7, modrm & 7
            if mod != 3 or rm != 0 or reg > 1:
                return None
            if op == 0xC0:
                imm = take()
                if imm is None:
                    return None
                ops.append(("rol" if reg == 0 else "ror", imm))
            else:
                ops.append(("inc" if reg == 0 else "dec",))
        elif op == 0xC3:
            return ops
        else:
            return None

def apply_ops(ops, x):
    """Run an op chain over a single byte."""
    for op in ops:
        name = op[0]
        if name == "add":
            x = (x + op[1]) & 0xFF
        elif name == "sub":
            x = (x - op[1]) & 0xFF
        elif name == "xor":
            x ^= op[1]
        elif name == "rol":
            n = op[1] & 7
            x = ((x << n) | (x >> (8 - n))) & 0xFF
        elif name == "ror":
            n = op[1] & 7
            x = ((x >> n) | (x << (8 - n))) & 0xFF
        elif name == "inc":
            x = (x + 1) & 0xFF
        elif name == "dec":
            x = (x - 1) & 0xFF
    return x
```

## Bijection and stub-discovery rules

* **256-byte lookup table:** every operation on `AL` is invertible (`add <-> sub`, `xor` self-inverse, `rol <-> ror`, `inc <-> dec`), so any valid program defines a bijection over `0..255` that precomputes into `lut = bytes(apply_ops(ops, i) for i in range(256))`.
* **Family-specific stub location:**
  * **Dedicated 64-bit DLL:** fixed offsets (`addr4 + 3200` for stub 1 and `addr5 + 12400` for stub 2).
  * **64-bit Stage 4 / classic Stage 5:** 16-byte-strided LFSR scan where the first valid parse with sufficient non-NOP instructions is the stub.
  * **PE32 `SevenStage`:** scans backward from `seven_dsz - 96` down to `seven_dsz / 2` before falling back to a forward scan.
  * **Marker-less 64-bit Stage 5 and PE32 `EighthStage`:** 1-byte-stepped LFSR scan where coincidental short valid parses can appear *before* the real stub; candidates are disambiguated by `fileCS` pointer proximity (`stub - 0x58` on 64-bit) and by replaying the first compressed section block through `decompress`.
