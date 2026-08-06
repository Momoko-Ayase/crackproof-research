---
description: Crackproof 对 Unity il2cpp 作品施加的可选 -GMD 混淆——global-metadata.dat 中的方法令牌被替换为稀疏值，只有受保护的加载器能在运行时将其映射回去。
---

# il2cpp 元数据混淆

独立于 PE 保护之外，Crackproof 提供一个选项（`-GMD`）来混淆 Unity il2cpp 作品的 **`global-metadata.dat`**。它只改变一样东西：每条 `Il2CppMethodDefinition` 记录的**方法令牌字段**。

## 它做了什么，以及为什么有效

il2cpp 解析方法的编译函数与调用器时，用 `(token_row - 1)` 索引每个模块的 `Il2CppCodeGenModule.methodPointers` / `invokerIndices` 表——这些表按模块的*已编译*方法数定长。这种索引只有当每个模块的方法令牌是**连续**区间 `1..=methodPointerCount` 时才成立。

`-GMD` 把连续令牌换成稀疏的、原生 .NET 元数据风格的值（在一部已观察作品中，核心库的行号达到约 55,000，而已编译方法只有约 14,000 个）。运行中的受保护游戏由加载器在加载时把它们映射回去，所以游戏能玩——但元数据文件单拎出来，就与 il2cpp 运行时的期望不一致了。

只要在受保护加载器之外消费这份元数据，问题就会显现：脱离加载器重映射启动的 il2cpp 映像按原值读令牌，`(token_row - 1)` 越过每模块表的末尾，进程在 il2cpp 初始化深处崩溃（首个受害者通常是 `System.Array` 的接口方法建立，表现为 `0xC0000005`）。解析 `global-metadata.dat` 的分析工具会看到指向编译表中不存在行的方法引用。

## 仅凭结构即可逆转

这种混淆不需要密钥，也不携带秘密——这意味着它可以从元数据自身的结构逆转。方法按类型分组布局，类型按映像（模块）分组，因此一个方法正确的令牌行号，就是它在其所属模块方法区间内的位置：

```
local_index = method_index - module_first_method_index
new_token   = 0x06000000 | ((local_index + 1) & 0x00FFFFFF)
```

只有方法令牌需要处理：字段令牌本就连续，类型令牌能正确解析。该变换是**幂等的**——在未混淆的元数据上，算出的令牌本就等于存储值，应用它等于无操作。

关键格式常量（元数据版本 31，Unity 2022.3 时代）：

| 项 | 值 |
| --- | --- |
| sanity 魔数（偏移 0） | `0xFAB11BAF` |
| 格式版本（偏移 4） | `31` |
| 头部表（offset/size i32 对） | methods `@0x30`、types `@0xA0`、images `@0xA8` |
| 结构步长 | method `0x24`、type `0x58`、image `0x28` |
| 字段 | method `.token +0x18`；type `.methodStart +0x24`、`.method_count +0x40`（u16）；image `.typeStart +0x08`、`.typeCount +0x0C` |

其他元数据版本使用不同的结构步长，必须按版本处理；把版本 31 的布局套到未知版本上会损坏文件，因此任何实现都应在写入任何一字节之前验证魔数、版本与各表对步长的整除性。
