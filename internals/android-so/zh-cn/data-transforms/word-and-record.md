---
description: "GF(2^32) 乘法、流头与记录描述符解密，以及 0x9D 加密描述符。"
icon: rotate
---

# 字、流与记录加解密

与 Windows 版的滚动异或不同，Android 版在流头、`0x5C` 字节记录描述符及 `0x9D` 加密描述符（`ProtectedDescriptor`）中使用 GF(2³²) 乘法与 32 位无符号模运算。

## GF(2³²) 定值乘法

`gf32_mul_fixed(value)` 先将输入截断为 32 位，再在模多项式 `0x579357EB` 定义的 GF(2³²) 上乘以固定常数 `0x94511DD2`：

```text
MASK32 = 0xFFFFFFFF

def gf32_mul_fixed(value):
    value &= MASK32
    multiplier = 0x94511DD2
    result = 0
    while multiplier:
        if multiplier & 1:
            result ^= value
        carry = value >> 31
        value = (value << 1) & MASK32
        if carry:
            value ^= 0x579357EB
        multiplier >>= 1
    return result
```

在本页的流头、记录描述符公式以及[容器头](container.md)公式中，`gf(x)` 均表示 `gf32_mul_fixed(x)`。

## 第一阶段按字解密

32 字节第一阶段参数头与加密的第二阶段映像均按字索引 `i` 和家族常量 `C`（`0xBF20165D` 或 `0xBF189BDD`）执行无符号 32 位回绕运算：

```text
plain[i] = ((cipher[i] + (i + 3) * key) ^ (C * (i + 1))) & MASK32
```

在 32 字节参数头中，第 `0` 个字给出 `key = cipher[0] ^ C`，待第 `1..7` 个字解码完毕后再回写为 `plain[0] = key`。各头部字段的校验条件见[第一阶段头部](../file-format/stage1.md)。

## 流头解密

每条解释器流（根层级为 `0xE2`，嵌套层级为 `0xE3`..`0xE8`）都以两个小端序双字（`cipher0`、`cipher1`）开头。目前已观察到两套常量家族；二者都将中间乘积与加法结果截断为 32 位，并由此导出 `dw0`（记录数量）和 `G`（该流的记录描述符种子）：

{% tabs %}
{% tab title="家族 A" %}
```text
K   = (sid * 0x9D323CD7) & MASK32
K   = ((K << (sid & 0xB)) + (K >> (sid & 7))) & MASK32
dw0 = (gf((cipher0 + 0xCBF0C1D8) & MASK32) ^ ((K + 0x4178CB33) & MASK32)) & MASK32
dw1 = (gf((cipher0 + cipher1) & MASK32)    ^ ((K + 0xF119421B) & MASK32)) & MASK32
G   = (K + 0x5590AD79 + dw1) & MASK32
```
{% endtab %}

{% tab title="家族 B" %}
```text
K   = (sid * 0x9D323CD7) & MASK32
mix = ((K >> (sid & 7)) + 0x5E727D74) & MASK32
mix = (mix + ((K << (sid & 0xB)) & MASK32) + 0xF71E3005) & MASK32
dw0 = (gf((cipher0 + 0xCBF0C1D8) & MASK32) ^ ((0xEBE81DBA + mix) & MASK32)) & MASK32
dw1 = (gf((cipher1 + cipher0) & MASK32)    ^ ((0xEBE81DBA * 5 + mix) & MASK32)) & MASK32
G   = (dw1 + mix) & MASK32
```
{% endtab %}
{% endtabs %}

解析时会依次尝试这两套家族常量，并以[第二阶段记录流](../file-format/stage2-streams.md)中的描述符结构校验作为判定依据。

## 记录描述符解密

每个 `0x5C` 字节记录描述符由 23 个小端序双字组成。给定流种子 `G` 与从 0 起算的记录下标 `idx`，两套家族共用同一解密循环：

```text
def rec_decrypt(G, idx, rec):
    product = ((G + 0x96F60B71) * G) & MASK32
    record_mask = (product << ((idx + 1) & 3)) & MASK32
    stream_mix = (G * 0x06A55BCC + product) & MASK32
    feedback = 0xF02F7685
    acc = 0x79934CF6
    for off in range(0, 0x5C, 4):
        cipher = get_u32(rec, off)
        square = (feedback * feedback) & MASK32
        value = gf32_mul_fixed(cipher ^ (square >> 3))
        value = (value ^ record_mask) & MASK32
        value = (value + acc + G) & MASK32
        value = (value - (stream_mix >> ((off + 3) & 5))) & MASK32
        put_u32(rec, off, value)
        acc = (acc + 0xE64D33D8) & MASK32
        feedback = cipher
```

{% hint style="warning" %}
`off` 每轮递增 4 字节，因此 `(off + 3) & 5` 会在 `1`（偶数字：`(0 + 3) & 5 = 1`）与 `5`（奇数字：`(4 + 3) & 5 = 5`）之间交替。`feedback` 每轮使用原始密文字 `cipher` 更新，而非解密后的明文 `value`。
{% endhint %}

## `0x9D` 加密描述符（`ProtectedDescriptor`）

直接记录模块 `0x9D` 开头是一个 `0x5C` 字节的 `ProtectedDescriptor`，使用[模块 `0x9B`](module-config.md) 提供的 `header_seed` 加密：

```text
def decrypt_protected_descriptor(data, seed):
    base0 = ((seed + 0xD3E87144) * seed) & MASK32
    base1 = (base0 + seed * 0x0BD9418D) & MASK32
    words = [0] * (0x5C // 4)
    for i in range(len(words)):
        cipher = get_u32(data, i * 4)
        sub = (base0 << (4 if i & 1 else 0)) & MASK32
        words[i] = ((cipher - sub) ^ (base1 >> ((seed + i * 4) & 7))) & MASK32
    return words
```

合法明文必须满足 `words[0] == 0x9D`（`command_id`）、`words[2] == 0x5C`（`outer_offset`，紧跟在描述符末尾之后）以及 `words[6..23] == 0`。第 `2..5` 个字分别给出主 ELF 映像容器的 `(outer_offset, outer_size)`，以及[容器变换](container.md)所述辅助重定位与符号容器的 `(aux_offset, aux_size)`。
