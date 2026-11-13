---
description: "0x8003 LFSR 存根流密码、按 RVA 派生的导入名解密与 .text 逐页代码混淆。"
icon: wave-square
---

# LFSR、字符串与代码页变换

## LFSR 密钥流（`dd6`） <a href="#lfsr-keystream-dd6" id="lfsr-keystream-dd6"></a>

每个 96 字节的[按构建生成的字节码存根](bytecode-transform.md)槽位在 `pos + 95` 处以明文保存指令长度（`<= 95`），并用固定种子的 Galois LFSR（初始状态 `1`，反馈多项式 `0x8003`，每字节按最低位优先输出 8 位）与 `d[pos .. pos + length]` 逐字节异或加密：

```python
def lfsr_keystream(n):
    out = bytearray(n)
    state = 1
    for i in range(n):
        b = 0
        for k in range(8):
            b |= (state & 1) << k
            state = (state << 1) & MASK32
            if state & 0x8000:
                state ^= 0x8003
        out[i] = b
    return out

def lfsr_decrypt_block(d, pos):
    """XOR a bytecode stub with the keystream. The block length is stored
    unencrypted at pos+95."""
    length = d[pos + 95]
    ks = lfsr_keystream(length)
    for i in range(length):
        d[pos + i] ^= ks[i]
```

由于密钥流仅取决于槽位内偏移 `0..length`，预先计算一张 95 字节的密钥流表即可在任意偏移处快速检测 96 字节候选窗口。

## 导入名字符串解密（`dd7`）

加密后的 DLL 名称与导入符号名称均以 NUL 结尾，解密时逐字节交换高四位与低四位（`ror8(..., 4)`）再减去 `key`；若差值为 `0`，则改取 `(-key) & 0xFF`，避免还原出提前截断字符串的 NUL 字节；每处理完一字节令 `key` 递增 `67`：

```python
def string_cipher(d, pos, key):
    """Decrypt a NUL-terminated string in place."""
    i = 0
    while d[pos + i] != 0:
        b = ror8(d[pos + i], 4)
        b = (b - key) & 0xFF
        if b == 0:
            b = (-key) & 0xFF
        d[pos + i] = b
        key = (key + 67) & 0xFF
        i += 1
```

{% hint style="warning" %}
**DLL 名称与导入函数名称的初始 `key` 差异。** 位于 `name_rva` 的 DLL 名称从 `pos = name_rva` 开始解密，初始密钥为 `key = name_rva & 0xFF`。按名称导入的符号则指向 `hint_name_rva` 处的 `IMAGE_IMPORT_BY_NAME` 结构，其 ASCII 符号名前带有 2 字节的 `Hint` 字段：字符串解密从 `pos = hint_name_rva + 2` 开始，但初始密钥仍取结构体起始 RVA 的低字节 `hint_name_rva & 0xFF`（切勿误取 `(hint_name_rva + 2) & 0xFF`）。
{% endhint %}

## 逐页代码混淆（`dd8`）

可执行代码节有时还叠加一层稀疏异或变换：在每个 4,096 字节页面的第 `1..255` 号 16 字节块中各异或修改 1 个字节（每页共修改 255 字节；第 `0` 号块仅步进 `key`，不执行异或）：

```python
def page_scramble(d, va, size, key):
    """64-bit form. `key` is the absolute page index shifted left by a
    build-specific amount (0 or 15)."""
    for i in range(size >> 4):
        mixed = (ror32(key, 15) + i) & MASK32
        key = (mixed + i) & MASK32
        if i == 0:
            continue
        d[va + i * 16 + (mixed & 0xF)] ^= key & 0xFF

def page_scramble_pe32(d, pa, page, big_formula):
    """32-bit form. The page key is (page+1) or 0x8000*(page+1)."""
    key = (0x8000 * (page + 1)) & MASK32 if big_formula else page + 1
    key = ror32(key, 15)
    for bi in range(1, 256):
        rk = ror32(key, 15)
        ri = (rk + bi) & MASK32
        key = (ri + bi) & MASK32
        d[pa + bi * 16 + (ri & 0xF)] ^= key & 0xFF
```

{% hint style="info" %}
**页面混淆模式的判定方法。** 容器头部并未记录 64 位移位量（`0`、`15` 或未混淆），也未记录 32 位页密钥公式（`page + 1`、`0x8000 * (page + 1)` 或未混淆），且不少原生 DLL 的 `.text` 节原本就未启用该混淆：
1. **64 位 CRT 入口指纹检查：** 对“原样不变”、“左移 `0`”和“左移 `15`”三种模式测试 18 字节 MSVC 入口存根（`48 83 EC ib / E8 rel32 / 48 83 C4 ib / E9 rel32`，且栈帧分配与回收立即数相同）；若仅有一种模式的 `call` 与 `jmp` 目标同时落在 `.text` 节范围内，直接选定该模式。
2. **64 位 `RET` + `int3` 函数尾声打分：** 若入口指纹未命中，则抽样 `.text` 中间页，统计 `0xC3`（`RET`）后紧跟至少 4 个 `0xCC` 填充字节的序列总字节长度，要求最高分比未处理基线至少多出 `8` 字节。
3. **修改位点的 `0xCC` 计数回退（64 位与 32 位）：** 64 位仅当三种模式的 `RET + int3` 得分全为 `0` 时启用（32 位始终采用此项），统计目标偏移处经异或还原后变为 `0xCC` 的字节数，要求至少达到未处理基线的 `2` 倍且不少于 `8` 处命中；否则保持 `.text` 原样不变。
{% endhint %}
