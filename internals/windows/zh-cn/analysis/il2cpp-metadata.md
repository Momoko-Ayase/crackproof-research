---
description: "还原 Unity IL2CPP 中无需密钥的 -GMD 方法 Token 稀疏混淆。"
icon: table
---

# il2cpp 元数据混淆

在 Unity IL2CPP 的 Windows 构建中，CrackProof 的可选 `-GMD` 模式会在保护主 PE（`GameAssembly.dll`）的同时修改 `global-metadata.dat`，改写每个 `Il2CppMethodDefinition` 表项中的 `token` 字段。

## 混淆机制与崩溃表现

IL2CPP 在启动时按 `(token & 0x00FFFFFF) - 1` 作为下标，索引 `Il2CppCodeGenModule.methodPointers` 与 `invokerIndices` 以解析各方法的编译后代码指针与调用器。由于这两个数组的长度恰好等于对应模块的已编译方法数，IL2CPP 要求每个模块内部的 `MethodDef` RID 必须构成从 `1..=methodPointerCount` 连续递增的紧凑序列。

`-GMD` 将原本连续的 RID 替换成了稀疏的 ECMA-335 风格 Token（例如某模块仅有约 `14,000` 个已编译方法，RID 却跳到了约 `55,000`）。在受保护进程内部，CrackProof 运行时会在 IL2CPP 读取元数据前先行重映射还原；若仅静态脱壳了 `GameAssembly.dll` 而未修复 `global-metadata.dat`，`il2cpp_init` 执行时 `(token_row - 1)` 就会发生数组越界（通常在初始化 `System.Array` 接口方法时触发 `0xC0000005` 崩溃）。

## 无需密钥的结构化还原

由于 `Il2CppMethodDefinition` 表中的行严格按所属类型（`Il2CppTypeDefinition`）连续成组存放，而类型又严格按所属模块（`Il2CppImageDefinition`）连续成组存放，每个方法的规范 Token 完全由其在表中的排列顺序唯一决定，还原无需任何密钥：

```text
local_index = method_index - image_first_method_index
new_token   = 0x06000000 | ((local_index + 1) & 0x00FFFFFF)
```

字段与类型的 Token 原本就是规范值，无需改动。对未混淆的 `global-metadata.dat` 执行上述计算时，`new_token` 与原有 `token` 完全相等，因此该还原变换天然幂等。

## 第 31 版元数据布局常量

| 项目 | 取值 |
| --- | --- |
| 头部校验魔数（`+0x00`） | `0xFAB11BAF` |
| 元数据版本号（`+0x04`） | `31` |
| 头部 `{offset, size}` 字段对 | `methods @0x30`、`types @0xA0`、`images @0xA8` |
| 单条记录步长 | `method = 0x24`、`type = 0x58`、`image = 0x28` |
| 关键字段偏移 | `method.token`（`+0x18` 处 `u32`）；`type.methodStart`（`+0x24` 处 `u32`）、`type.method_count`（`+0x40` 处 `u16`）；`image.typeStart`（`+0x08` 处 `u32`）、`image.typeCount`（`+0x0C` 处 `u32`） |

写入还原字节前，务必依次核验 `0xFAB11BAF` 魔数、`version == 31`、各表范围未超出文件边界、表大小能被记录步长整除，以及每个模块所辖方法区间连续不重叠。Android 平台的 IL2CPP 构建则采用带种子的五轮 RID 或 `methodIndex` 置换，由子模块 `0x0C` 负责还原（在第 31 版元数据上也将 `-GMD` 作为回退方案）；详见 [方法 Token 混淆](https://app.gitbook.com/s/Aoyn9wKiHAVzBKGSUifa/metadata/method-tokens)。
