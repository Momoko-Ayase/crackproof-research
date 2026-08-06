---
description: "容器格式、加载器与运行时各处使用的常量、偏移与编码速查表。"
---

# 附录：常量与偏移

## 格式 magic

| magic | 值 | 含义 |
| --- | --- | --- |
| `KONN` | `0x4E4E4F4B` | 受支持的容器戳 |
| `KNKN` | `0x4E4B4E4B` | 受支持的容器戳（算法一致） |
| `CUSN` | `0x4E535543` | 已知的第三种戳；布局不兼容 |

## 容器常量

| 项 | 值 |
| --- | --- |
| 头区大小 / info 头偏移 | `4096`（`0x1000`） |
| info 头大小 | 32 字节（8 个 dword） |
| 最小识别长度 | 4128 字节 |
| `decrypt_size`（payload 链长度） | `info[6] - info[3] + 8192` |
| 节数据文件基址 | `(~u32@0x1080) + 0x1000` |
| 伴生体配对检查 | `stub[4096..4128] == companion[0..32]` |
| 文件完整性 dword | `u32@0x38 + 0x76543211`（混淆存储于偏移 `0x38`） |
| 配置簇版本戳（32 位） | `0x00007679` |
| stage-5 标记（64 位标记布局） | `70 6D 00 00 63 6D 00 00` 与 `00 00 00 40 01 00 00 00` |

## 原语速查

| 原语 | 公式 |
| --- | --- |
| 头部 KDF | `info[i+1] = k ^ cell; k = i² ^ (k + cell − i)` |
| payload 链 | `out = k ^ cell; k = i² ^ (k + cell + i)` |
| XOR-ROR dword 密码 | `v = x ^ key; key += i; out = ror(v, shift) − i`（shift 19/21） |
| 字节 rotate-3 | 三次 `rol3`，间插 XOR `b2`、`b`；密钥逐字节 +1 |
| 字节 rotate-2 | 三次 `rol2`，间插 XOR `b2`、`b`；以地址低字节为钥 |
| LFSR | 种子 1，反馈 `0x8003`，每字节 8 位 LSB 优先；块长度在 `+95` |
| 字符串密码 | `ror4(b) − key`（0 → `−key`），`key += 67` 逐字节 |
| 页扰动（64 位） | `mixed = ror15(key)+i; key = mixed+i; page[i*16 + (mixed&0xF)] ^= key`，块 0 只推进 |
| 页扰动（32 位） | 同循环，前置 `key = ror15(pk)`；`pk = page+1` 或 `0x8000*(page+1)` |
| CRC-32 | 反射，多项式 `0xEDB88320` |
| 校验和描述符 | `crc32(region) ^ length` |
| 三角数调度 | 每轮 `m`：`key += 1..(m+1)*100` |
| AES | CBC 解密；轮数为调度表+2 处 u16；状态大端；标准逆 T 表 |

## PE 字段偏移

| 字段 | PE32+ | PE32 |
| --- | --- | --- |
| `AddressOfEntryPoint` | `pe + 0x28` | `pe + 0x28` |
| 数据目录基址 | `pe + 0x88`（136） | `pe + 0x78`（120） |
| 导入目录（DD[1]） | `pe + 0x90` | `pe + 0x80` |
| 基址重定位（DD[5]） | `pe + 0xB0` | `pe + 0xA0` |
| TLS（DD[9]） | `pe + 0xD0` | `pe + 0xC0` |
| IAT（DD[12]） | `pe + 0xE8` | `pe + 0xD8` |
| CLR/COM 描述符（DD[14]） | `pe + 0xF8` | `pe + 0xE0` |
| `DllCharacteristics` | `pe + 0x5E` | `pe + 0x5E` |
| `SizeOfImage` | `pe + 0x50` | `pe + 0x50` |
| `IMAGE_FILE_DLL` 位 | Characteristics（`pe + 0x16`）中的 `0x2000` | 相同 |

## 字节码 stub 操作码表

| 字节 | 指令 | 操作 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | add |
| `2C ib` | `SUB AL, imm8` | sub |
| `34 ib` | `XOR AL, imm8` | xor |
| `90` | `NOP` | 无 |
| `C0 /0 ib` | `ROL AL, imm8` | rol |
| `C0 /1 ib` | `ROR AL, imm8` | ror |
| `FE /0` | `INC AL` | inc |
| `FE /1` | `DEC AL` | dec |
| `C3` | `RET` | 结束 |

ModR/M 必须是寄存器直接寻址的 `AL`（`mod=3, rm=0`）；其余一律无效。

## 交叉引用

- 状态码与启动序列：[运行时行为](runtime-behavior.md#启动序列与状态码)
- 模块代码与驱动世代：[内核驱动与子模块](kernel-components.md)
- il2cpp 元数据常量：[il2cpp 元数据混淆](il2cpp-metadata.md)
- Huffman 表/token 格式：[数据变换原语](primitives.md#huffmanlz-压缩格式)

## 验证套件

本文档中的每个 Python 片段在发布前都经过验证：每个函数的输出在相同输入上与算法的独立参考移植逐字节比对（30 个测试向量，全部一致）。完整可运行的片段文件与比对工具发布在本站的[验证与参考](https://launchcore.gitbook.io/crackproof-research/reference/)栏目中——运行 `python run_tests.py` 可重跑全部比对。
