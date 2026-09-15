---
description: "识别受支持的 IL2CPP 元数据版本，并还原各 image 的方法 RID 置换。"
---

# 方法令牌

已识别的 IL2CPP 元数据魔数是 `0xFAB11BAF`。受支持的布局为版本 29、31 与 39，三者共享下文介绍的带种子五轮 RID 置换。MethodDef 令牌高字节为表号 `0x06`，低 24 位是行标识。

这不是 Windows 的 `-GMD` 重映射。Windows 把每个令牌换成仅由表格顺序得到的连续值 `0x06000000 | (local_index + 1)`。Android 路径是对每个 image 方法块内部 RID 做带种子的五轮置换。Windows 规则见 [il2cpp 元数据混淆](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/analysis/il2cpp-metadata)。

## image 区间

对每个原生 image，受保护的方法块是一段连续 RID 区间。各区间不得重叠，必须覆盖已声明的方法记录，并构成期望 image 顺序的一个置换。落在区间外的令牌或重复 RID 会被拒绝。

种子取自受保护记录（模块 `0x0C`），不是从相邻方法推断。一个已观察的默认值是 `0xa6fae968`。还原之后再次检查元数据头、表偏移、字符串区间和方法令牌引用。

在 IL2CPP 库上，同一清理也在加载时发生：模块 `0x0C` 用 hook 替换 `mmap`，并在进程映射 `global-metadata.dat` 时还原令牌。同一家族的原生库不携带 `0x0C`。见[运行时模块](../runtime/modules.md)。

## 五轮逆变换

设 `low`/`high` 是某个 image 的闭区间 RID 界，`count = high - low + 1`（`count ≥ 2`），`key = (seed % (count / 2)) + count / 4`。对加密 RID `rid`：

```
value = rid - low
repeat 5 times:
    mirror = count * 2 - 1
    if value is odd: value = mirror - value
    value >>= 1
    if value >= count: value = mirror - value
    value = value - key          (mod 2^32 wrap)
    if value > count: value = value + count
rid' = value + low
```

新令牌是 `0x06000000 | rid'`。对工具而言清理是幂等的：若各令牌已经是按 image 的规范顺序，则检测出来并保持不动，而不是再做一次逆变换。

表常量因版本而异。版本 29 与 31 的 type 和 image 布局与 Windows 版本 31 表相同（types `@0xA0` 步长 `0x58`，images `@0xA8` 步长 `0x28`；type `.methodStart +0x24` / `.method_count +0x40`，image `.typeStart +0x08` / `.typeCount +0x0C`），仅方法行不同：

| 版本 | 方法表 | 方法步长 | `.token` 偏移 |
| --- | --- | --- | --- |
| 29 | `@0x30` | `0x20` | `+0x14` |
| 31 | `@0x30` | `0x24` | `+0x18` |

版本 39 用 12 字节 `(offset, size, count)` 节记录表取代固定头部，并使用变宽索引（1、2 或 4 字节，按各表的 count 选取）；其方法、类型与 image 步长由这些宽度推导。其他任何版本都必须拒绝，而不是用错误的布局解码。
