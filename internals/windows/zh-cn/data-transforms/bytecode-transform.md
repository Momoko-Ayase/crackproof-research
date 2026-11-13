---
description: "按构建生成的九操作码 AL x86 字节码存根、256 字节查找表预计算与定位规则。"
icon: microchip
---

# 按构建生成的字节变换

## 按构建生成的 `AL` 字节码置换

加壳时，CrackProof 会为每次构建随机生成两段短小的 x86 函数：函数从 `AL` 接收单字节输入，依次执行一串算术与循环移位指令后以 `RET` 返回。其中存根 1 用于解码最后一个加载器阶段，存根 2 在 AES-CBC 解密之后、Huffman/LZ 解压之前解码每一个节数据块。

每个存根占用 96 字节槽位，由 [LFSR 密钥流](lfsr-strings-pages.md#lfsr-keystream-dd6)异或加密（明文指令字节长度存放在 `+95` 处）。指令流中仅会出现以下九种 x86 编码：

| 机器码 | x86 指令 | 解析后的操作 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | 跳过 |
| `C0 C0 ib`（`mod=3, reg=0, rm=0`） | `ROL AL, imm8` | `("rol", imm)` |
| `C0 C8 ib`（`mod=3, reg=1, rm=0`） | `ROR AL, imm8` | `("ror", imm)` |
| `FE C0`（`mod=3, reg=0, rm=0`） | `INC AL` | `("inc",)` |
| `FE C8`（`mod=3, reg=1, rm=0`） | `DEC AL` | `("dec",)` |
| `C3` | `RET` | 函数返回（结束解析） |

遇到任何其他操作码或不符合约束的 `ModR/M` 字节，即判定该候选槽位无效。

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

## 双射性质与各构建类型的存根定位规则

* **256 字节查找表：** 对 `AL` 的每一步操作均在 `0..255` 上可逆（`add <-> sub` 互逆，`xor` 自逆，`rol <-> ror` 互逆，`inc <-> dec` 互逆），因此任何合法存根都构成 `0..255` 上的双射，可一次性预计算为查找表 `lut = bytes(apply_ops(ops, i) for i in range(256))`。
* **各构建类型的存根定位方式：**
  * **专用 64 位 DLL：** 位于固定偏移（存根 1 在 `addr4 + 3200`，存根 2 在 `addr5 + 12400`）。
  * **64 位 Stage 4 / 经典有标记 Stage 5：** 按 16 字节步长执行 LFSR 扫描，首个包含足够数量非 `NOP` 指令的合法解析结果即为目标存根。
  * **PE32 `SevenStage`：** 先从 `seven_dsz - 96` 倒序扫描至 `seven_dsz / 2`，未命中时再回退至正向扫描。
  * **无标记 64 位 Stage 5 与 PE32 `EighthStage`：** 按 1 字节步长逐字节执行 LFSR 扫描。由于真实存根前方可能巧合出现短小的合法指令序列，需结合 `fileCS` 指针的相对距离（64 位位于 `stub - 0x58`）并对首个压缩节数据块执行试探 `decompress` 来排除误命中候选。
