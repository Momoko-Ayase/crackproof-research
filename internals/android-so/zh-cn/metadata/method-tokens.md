---
description: "带种子的 MethodDef RID 五轮逆置换与 v24.1 methodIndex 还原。"
icon: hashtag
---

# 方法令牌

标准 IL2CPP 元数据文件以校验魔数 `0xFAB11BAF` 开头，后跟 32 位版本号。在 Android 平台上，CrackProof 在版本 `29`、`31` 和 `39` 中对按镜像（image）划分的 `MethodDef` RID（`0x06000000 | rid`）施加带种子的五轮对称减法置换；在版本 `24`（`v24.1`）中则对全局 `methodIndex` 表项施加同类置换，并配合一张 256 项例外表。部分版本 `31` 构建改用无密钥的 `-GMD` 令牌布局。

如需对比 Windows 端无密钥的 `-GMD` 重映射（仅按表顺序将稀疏令牌替换为 `0x06000000 | (local_index + 1)`），请参阅 [IL2CPP 元数据混淆](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/analysis/il2cpp-metadata)。

## 五轮逆置换

给定包含 `count` 个连续表项的区间（`count >= 2`）与 32 位 `seed`，先计算 `key = (seed % (count // 2)) + (count // 4)` 和 `mirror = count * 2 - 1`。每个从 0 起算的下标 `value`（`0 <= value < count`）按 32 位无符号回绕运算（`MASK32 = 0xFFFFFFFF`）重复执行五轮逆变换：

```text
repeat 5 times:
    if value & 1:
        value = mirror - value
    value >>= 1
    if value >= count:
        value = mirror - value
    value = (value - key) & MASK32
    if value > count:
        value = (value + count) & MASK32
```

对于版本 `29`、`31` 和 `39` 的 `MethodDef` 令牌，在每个镜像的闭区间 RID 范围 `[low, high]` 内取 `value = rid - low`，还原后的令牌为 `0x06000000 | (value + low)`。由于未混淆的元数据在每个镜像内的 RID 本身就是连续的 `1..=count`，还原前会先检查当前镜像是否已按 `1..=count` 连续递增排列，若是则直接跳过，避免改动未混淆的输入。

## 各版本布局与种子恢复

{% tabs %}
{% tab title="版本 29 与 31" %}
版本 `29` 和 `31` 使用固定文件头 `{offset, size}` 字段对，且共用相同的类型与镜像描述符布局：

* **类型表（`@0xA0`，步长 `0x58`）：** `methodStart`（`+0x24` 处的 `u32`）、`method_count`（`+0x40` 处的 `u16`）。
* **镜像表（`@0xA8`，步长 `0x28`）：** `typeStart`（`+0x08` 处的 `u32`）、`typeCount`（`+0x0C` 处的 `u32`）。
* **方法表（`@0x30`）：**
  * **版本 29：** 步长 `0x20`，`token`（`u32`）位于 `+0x14`。
  * **版本 31：** 步长 `0x24`，`token`（`u32`）位于 `+0x18`。

运行时，模块 `0x0C` 会 hook `mmap` 并应用其内置种子（已观测到的默认值为 `0xA6FAE968`）。对于版本 `29`、`31` 和 `39`，静态还原无需依赖模块 `0x0C`：每个镜像仅有 `count / 2` 个候选 `key` 余数，逐一测试候选值能否还原出 `1..=count` 的连续递增顺序，再对各镜像得到的 `seed % (count / 2)` 同余约束求交集，即可直接从 `global-metadata.dat` 恢复出有效种子。若各镜像未产生有效约束，则默认取 `0xA6FAE968`；采用 `-GMD` 保护的版本 `31` 构建则改用按表项顺序的 `0x06000000 | (local_index + 1)` 重映射。
{% endtab %}

{% tab title="版本 39（紧凑目录）" %}
版本 `39` 将固定文件头偏移替换为由 12 字节 `{offset, size, count}` 节描述符组成的紧凑目录，并采用变长表索引：

* `type_definition`、`parameter` 和 `generic_container` 索引的宽度按表项数量取值：`1` 字节（`count <= 255`）、`2` 字节（`count <= 65535`）或 `4` 字节（`count > 65535`）。
* `type_index` 的宽度由第 `18` 节（`interface_offsets`）推算：`count == 0` 时为 `4` 字节，否则为 `(size / count) - 4`。

方法表、类型表和镜像表的记录步长与字段偏移均由这四个索引宽度算出；随后的单镜像余数求解与五轮 RID 逆置换流程保持不变。
{% endtab %}

{% tab title="版本 24.1（methodIndex + 0x0C）" %}
符合 `v24.1` `Il2CppMethodDefinition` 布局（步长 `0x34`，有符号 `i32` `methodIndex` 位于 `+0x14`）的外部版本 `24` 元数据不会改动 `MethodDef` 令牌，而是置换全部非负 `methodIndex` 表项（`0..active_count`，其中 `active_count > 256`）：

1. 全部 `active_count` 个非负 `methodIndex` 槽位以 `key = (seed % (active_count // 2)) + (active_count // 4)` 执行五轮置换。
2. 前 256 个有效槽位的值单独存放在模块 `0x0C` 内的 256 项 `u32` 例外表中。

因此，静态还原需要将元数据文件与所属应用解码出的模块 `0x0C` 配对，在 `0x0C` 内定位 `{u32 seed, u32 24}` 和 `{u32 1, u32 active_count - 1}` 头部标记以及 256 项例外表，先还原这 256 个例外项，再对全部 `active_count` 个有效方法执行五轮逆置换。
{% endtab %}
{% endtabs %}

## 还原后校验

重映射完成后，校验流程会确认镜像表、类型表和方法表均未超出文件边界，每个方法按连续表顺序恰好归属于唯一镜像，每个 `MethodDef` 令牌均带有表前缀 `0x06000000` 且局部 RID 从 `1` 连续递增（或在 `v24.1` 上完整覆盖 `0..active_count`），且不存在越界或重复表项。
