---
description: "定義構建專用字節置換的緊湊指令流。"
---

# 按構建定製的字節變換

## 按構建定製的字節碼置換

最有辨識度的一層：CrackProof 不為 payload 數據硬編碼固定的逐字節變換。加殼時它**為每個構建生成一段獨有的 x86 stub**——一個在 `AL` 中接收一個字節、施加一小段隨機算術/移位指令序列後返回的函數。加載器在分組密碼之後、解壓之前，對 payload 的每個字節運行這段 stub。因此來自不同構建的兩個受保護文件不共享任何 payload 置換。

stub 以上述 LFSR 密鑰流包裹存儲。實際出現的指令只有一個很窄的子集：

| 字節 | x86 指令 | 解碼操作 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | 跳過 |
| `C0 /0 ib` | `ROL AL, imm8` | `("rol", imm)` |
| `C0 /1 ib` | `ROR AL, imm8` | `("ror", imm)` |
| `FE /0` | `INC AL` | `("inc",)` |
| `FE /1` | `DEC AL` | `("dec",)` |
| `C3` | `RET` | 程序結束 |

對 `C0`/`FE`，ModR/M 字節必須編碼寄存器直接尋址的 `AL`（`mod=3, rm=0`）；reg 字段選擇子操作。其餘一律解析失敗——正是這種嚴格性讓候選 stub 位置的試解碼可靠：解出的垃圾數據幾乎不可能解析為以 `RET` 結尾的合法程序。

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

由此直接得到兩個結構性質：

- **整條鏈是 256 字節值空間上的一個置換。** 每個 op 都可逆（`add↔sub`、`xor` 自逆、`rol↔ror`、`inc↔dec`），所以整個映射是雙射。可以預計算成一張 256 項翻譯表（`bytes(apply_ops(ops, i) for i in range(256))`）；沿 op 列表逆序、每個 op 換成其逆 op，即得逆鏈。
- **定位 stub 是搜索問題，而非固定偏移。** 由於密鑰流與數據無關，對候選位置做試 XOR 並解析即可；能解碼為合法程序（含足夠真實操作、以 `RET` 終止）的最低位置就是真 stub。更靠後的合法解析多是尾部填充字節的巧合解碼。

一個構建攜帶**兩個**這樣的 stub：一個用於解密最終加載器階段，另一個獨立的應用於每個節數據塊。

