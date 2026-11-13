---
description: "ビルド別の9命令ALバイトコードスタブ、256バイトLUT事前計算、系統別のスタブ探索。"
icon: microchip
---

# ビルド別のバイト変換

## ビルド別の `AL` バイトコード置換

CrackProof はパック時に、`AL` レジスタで 1 バイトを受け取り、ランダムな算術演算とビット回転命令の列を適用して `RET` で返る短い x86 関数をビルドごとに 2 つ生成します。1 つ目のバイトコードスタブは最終ローダーステージの復号に使われ、2 つ目のバイトコードスタブは各セクションのペイロードブロックに対して AES-CBC 復号後・ハフマン / LZ 展開前に適用されます。

各バイトコードスタブは [LFSR キーストリーム](lfsr-strings-pages.md#lfsr-keystream-dd6)でマスクされた 96 バイトのスロットを占め、オフセット `+95` にはプログラム本体のバイト長が未暗号化のまま格納されています。出現する x86 命令エンコーディングは以下の 9 種類のみです。

| バイト列 | x86 命令 | デコード結果 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | スキップ |
| `C0 C0 ib` (`mod=3, reg=0, rm=0`) | `ROL AL, imm8` | `("rol", imm)` |
| `C0 C8 ib` (`mod=3, reg=1, rm=0`) | `ROR AL, imm8` | `("ror", imm)` |
| `FE C0` (`mod=3, reg=0, rm=0`) | `INC AL` | `("inc",)` |
| `FE C8` (`mod=3, reg=1, rm=0`) | `DEC AL` | `("dec",)` |
| `C3` | `RET` | プログラム終端 |

これ以外のオペコードや `ModR/M` バイトが現れた場合、その候補スロットは無効として棄却されます。

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

## 全単射性とスタブ探索ルール

* **256 バイトのルックアップテーブル：** `AL` に対する各演算はいずれも可逆（`add <-> sub`、自己逆元の `xor`、`rol <-> ror`、`inc <-> dec`）であるため、有効な命令列はすべて `0..255` 上の全単射を定義します。したがって `lut = bytes(apply_ops(ops, i) for i in range(256))` として 256 バイトの変換テーブルを事前計算できます。
* **ビルド系統別のスタブ配置：**
  * **専用 64 ビット DLL：** 固定オフセット（スタブ 1 は `addr4 + 3200`、スタブ 2 は `addr5 + 12400`）に配置されます。
  * **64 ビット Stage 4 / 従来型 Stage 5：** 16 バイト刻みの LFSR スキャンを行い、十分な数の非 `NOP` 命令を含む最初の有効なパース結果をスタブとして採用します。
  * **PE32 `SevenStage`：** `seven_dsz - 96` から `seven_dsz / 2` まで逆方向にスキャンし、見つからない場合のみ順方向スキャンへフォールバックします。
  * **マーカーなし 64 ビット Stage 5 および PE32 `EighthStage`：** 1 バイト刻みの LFSR スキャンを行います。本物のスタブより**手前に**偶然短い有効な命令列としてパースできるバイト列が現れることがあるため、`fileCS` ポインターとの距離（64 ビットでは `stub - 0x58`）および最初の圧縮セクションブロックに対する `decompress` の試行実行によって本物のスタブを特定します。
