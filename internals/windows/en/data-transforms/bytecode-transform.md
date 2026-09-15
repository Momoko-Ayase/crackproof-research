---
description: "The compact instruction stream that defines a build-specific byte permutation."
---

# Per-build byte transform

## The per-build bytecode permutation

The most distinctive layer: CrackProof doesn't hardcode a fixed per-byte transform for payload data. At pack time it **generates a unique x86 stub for each build**, a function that takes one byte in `AL`, applies a short random sequence of arithmetic/rotate instructions, and returns. The loader runs this stub over every payload byte between the block-cipher pass and decompression. Two protected files from different builds therefore share no payload permutation.

The stub is stored wrapped in the [LFSR keystream](lfsr-strings-pages.md#the-lfsr-keystream). Only a narrow instruction subset ever appears:

| Bytes | x86 instruction | Decoded op |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | skipped |
| `C0 /0 ib` | `ROL AL, imm8` | `("rol", imm)` |
| `C0 /1 ib` | `ROR AL, imm8` | `("ror", imm)` |
| `FE /0` | `INC AL` | `("inc",)` |
| `FE /1` | `DEC AL` | `("dec",)` |
| `C3` | `RET` | end of program |

For `C0`/`FE` the ModR/M byte must encode register-direct `AL` (`mod=3, rm=0`); the reg field selects the sub-operation. Anything else fails the parse, and that strictness is what makes trial-decoding candidate stub locations reliable: decrypted garbage essentially never parses as a valid program ending in `RET`.

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

Two structural properties follow directly:

- **The chain is a permutation of the 256 byte values.** Every op is reversible (`add↔sub`, `xor` self-inverse, `rol↔ror`, `inc↔dec`), so the whole map is a bijection. It can be precomputed as a 256-entry translation table (`bytes(apply_ops(ops, i) for i in range(256))`), and an inverse chain exists by walking the op list backwards with each op swapped for its inverse.
- **Finding the stub is a search problem, not a fixed offset.** Because the keystream is data-independent, candidate positions are trial-XORed and parsed; the lowest position that decodes to a valid program (enough real operations, terminating in `RET`) is the real stub. Later valid parses are coincidental decodes of trailing filler.

One build carries **two** such stubs: one used while decrypting the final loader stage, and a second, independent one applied to every section data block.
