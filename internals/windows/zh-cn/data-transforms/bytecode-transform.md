---
description: "定义构建专用字节置换的紧凑指令流。"
---

# 按构建定制的字节变换

## 按构建定制的字节码置换

最有辨识度的一层：CrackProof 不为 payload 数据硬编码固定的逐字节变换。加壳时它**为每个构建生成一段独有的 x86 stub**——一个在 `AL` 中接收一个字节、施加一小段随机算术/移位指令序列后返回的函数。加载器在分组密码之后、解压之前，对 payload 的每个字节运行这段 stub。因此来自不同构建的两个受保护文件不共享任何 payload 置换。

stub 以上述 LFSR 密钥流包裹存储。实际出现的指令只有一个很窄的子集：

| 字节 | x86 指令 | 解码操作 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | 跳过 |
| `C0 /0 ib` | `ROL AL, imm8` | `("rol", imm)` |
| `C0 /1 ib` | `ROR AL, imm8` | `("ror", imm)` |
| `FE /0` | `INC AL` | `("inc",)` |
| `FE /1` | `DEC AL` | `("dec",)` |
| `C3` | `RET` | 程序结束 |

对 `C0`/`FE`，ModR/M 字节必须编码寄存器直接寻址的 `AL`（`mod=3, rm=0`）；reg 字段选择子操作。其余一律解析失败——正是这种严格性让候选 stub 位置的试解码可靠：解出的垃圾数据几乎不可能解析为以 `RET` 结尾的合法程序。

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

由此直接得到两个结构性质：

- **整条链是 256 字节值空间上的一个置换。** 每个 op 都可逆（`add↔sub`、`xor` 自逆、`rol↔ror`、`inc↔dec`），所以整个映射是双射。可以预计算成一张 256 项翻译表（`bytes(apply_ops(ops, i) for i in range(256))`）；沿 op 列表逆序、每个 op 换成其逆 op，即得逆链。
- **定位 stub 是搜索问题，而非固定偏移。** 由于密钥流与数据无关，对候选位置做试 XOR 并解析即可；能解码为合法程序（含足够真实操作、以 `RET` 终止）的最低位置就是真 stub。更靠后的合法解析多是尾部填充字节的巧合解码。

一个构建携带**两个**这样的 stub：一个用于解密最终加载器阶段，另一个独立的应用于每个节数据块。

