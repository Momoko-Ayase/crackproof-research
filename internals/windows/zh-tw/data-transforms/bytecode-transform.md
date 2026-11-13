---
description: "隨組建生成的九指令 AL x86 位元組碼存根、256 位元組查表與各家族存根定位規則。"
icon: microchip
---

# 隨組建生成的位元組轉換

## 隨組建生成的 `AL` 位元組置換

加殼時，CrackProof 會針對每次組建合成兩段簡短的 x86 函式：兩者皆由 `AL` 接收單一位元組，依序執行一串隨機組合的算術與位元旋轉指令後返回（`RET`）。其中第一段存根用於解碼最後一個載入器階段，第二段存根則在 AES-CBC 解密後、Huffman/LZ 解壓縮前解碼每一個區段負載區塊。

每段存根佔用一個 96 位元組槽位，並以 [LFSR 金鑰流](lfsr-strings-pages.md#lfsr-keystream-dd6)遮罩（程式實際位元組長度以明文存於 `+95`）。存根內僅會出現九種 x86 指令編碼：

| 位元組 | x86 指令 | 解碼後的操作 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | 略過 |
| `C0 C0 ib`（`mod=3, reg=0, rm=0`） | `ROL AL, imm8` | `("rol", imm)` |
| `C0 C8 ib`（`mod=3, reg=1, rm=0`） | `ROR AL, imm8` | `("ror", imm)` |
| `FE C0`（`mod=3, reg=0, rm=0`） | `INC AL` | `("inc",)` |
| `FE C8`（`mod=3, reg=1, rm=0`） | `DEC AL` | `("dec",)` |
| `C3` | `RET` | 程式結束 |

只要遇到任何其他 opcode 或不符上述條件的 `ModR/M` 位元組，該候選槽位即視為無效。

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

## 雙射性質與存根定位規則

* **256 位元組查表：** 對 `AL` 的每種基本運算皆可逆（`add <-> sub`、`xor` 自反、`rol <-> ror`、`inc <-> dec`），因此任何合法存根都在 `0..255` 上定義一組雙射，可預先算成 `lut = bytes(apply_ops(ops, i) for i in range(256))` 直接查表轉換。
* **各家族的存根位置：**
  * **64 位元專用 DLL：** 固定位移（存根 1 位於 `addr4 + 3200`，存根 2 位於 `addr5 + 12400`）。
  * **64 位元 Stage 4／早期帶標記 Stage 5：** 以 16 位元組步進執行 LFSR 掃描，第一個合法且非 `NOP` 指令數足夠的解析結果即為目標存根。
  * **PE32 `SevenStage`：** 先從 `seven_dsz - 96` 往回掃描至 `seven_dsz / 2`，若未命中再退回正向掃描。
  * **無標記 64 位元 Stage 5 與 PE32 `EighthStage`：** 以 1 位元組步進執行 LFSR 掃描。由於真實存根前方可能巧合出現極短但語法合法的偽陽性片段，需搭配 `fileCS` 指標距離（64 位元為 `stub - 0x58`）排序，並將第一個壓縮區段區塊實際送入 `decompress` 驗證來排除誤判。
