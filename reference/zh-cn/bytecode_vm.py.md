---
description: "逐构建的自定义字节变换：x86 桩解码器、解释器、翻译表与逆变换链。"
---

# bytecode\_vm.py

解码每个构建独有 x86 桩的字节码 VM，见[数据变换原语](https://launchcore.gitbook.io/crackproof-research/docs/primitives#the-per-build-bytecode-permutation)。

```python
"""The per-build custom byte transform ("bytecode VM").

Each protected build generates a unique x86 stub: it takes one byte in AL,
applies a short sequence of arithmetic/rotate instructions, and returns.
The loader runs this stub over every payload byte between the block-cipher
pass and decompression.

Instead of executing x86, the instruction bytes are decoded into a tiny op
list and interpreted. Every op is reversible (add/sub, xor, rol/ror,
inc/dec), so the whole chain is a permutation of the 256 byte values and
can be precomputed as a 256-entry translation table.

Only a narrow instruction subset ever appears; anything else fails the
parse, which is what makes trial-decoding candidate locations reliable.
"""

# Opcode map: x86 encoding -> VM operation.
#   04 ib        ADD AL, imm8        ("add", imm)
#   2C ib        SUB AL, imm8        ("sub", imm)
#   34 ib        XOR AL, imm8        ("xor", imm)
#   90           NOP                 (skipped)
#   C0 /0 ib     ROL AL, imm8        ("rol", imm)
#   C0 /1 ib     ROR AL, imm8        ("ror", imm)
#   FE /0        INC AL              ("inc",)
#   FE /1        DEC AL              ("dec",)
#   C3           RET                 end of program
#
# For C0/FE the ModR/M byte must encode register-direct AL (mod=3, rm=0);
# the reg field selects the sub-operation.


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
        if op == 0x04:  # ADD AL, imm8
            imm = take()
            if imm is None:
                return None
            ops.append(("add", imm))
        elif op == 0x2C:  # SUB AL, imm8
            imm = take()
            if imm is None:
                return None
            ops.append(("sub", imm))
        elif op == 0x34:  # XOR AL, imm8
            imm = take()
            if imm is None:
                return None
            ops.append(("xor", imm))
        elif op == 0x90:  # NOP
            pass
        elif op in (0xC0, 0xFE):
            modrm = take()
            if modrm is None:
                return None
            mod, reg, rm = modrm >> 6, (modrm >> 3) & 7, modrm & 7
            if mod != 3 or rm != 0 or reg > 1:
                return None
            if op == 0xC0:  # ROL/ROR AL, imm8
                imm = take()
                if imm is None:
                    return None
                ops.append(("rol" if reg == 0 else "ror", imm))
            else:  # INC/DEC AL
                ops.append(("inc" if reg == 0 else "dec",))
        elif op == 0xC3:  # RET
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


def build_translation_table(ops):
    """The op chain is a pure function of one byte, so precompute all 256
    results once and translate whole regions by table lookup."""
    return bytes(apply_ops(ops, i) for i in range(256))


def inverse_ops(ops):
    """Reverse the chain: walk backwards, swapping each op for its inverse.
    (Documents why the transform is a permutation - it can always be undone.)"""
    inverse = {"add": "sub", "sub": "add", "xor": "xor",
               "rol": "ror", "ror": "rol", "inc": "dec", "dec": "inc"}
    return [(inverse[op[0]], *op[1:]) for op in reversed(ops)]
```
