---
description: "文件魔数、容器公式、加解密与校验计算式、PE32/PE32+ 字段偏移及字节码操作码速查表。"
icon: sliders
---

# 常量与偏移速查

## 容器常量与魔数

| 项目 | 取值 |
| --- | --- |
| 格式魔数（`info[1]`） | `0x4E4E4F4B`（小端序 ASCII `KONN`） |
| 外层 PE 头部区域长度 / `info` 偏移 | `4096`（`0x1000`） |
| 加密 `info` 头部长度 | `32` 字节（`8` 个双字） |
| 候选文件最小长度 | `4128`（`0x1020`）字节 |
| `decrypt_size`（标准版 / 完整载荷 PE32） | `info[6] - info[3] + 8192` / `info[5]`（紧凑型 PE32 回退值） |
| 节数据文件基偏移 | `(~u32@0x1080 + 0x1000) & 0xFFFFFFFF` |
| 伴生文件（`._`）配对校验 | `stub[4096..4128] == companion[0..32]` |
| 伴生文件入口桩标记（`+53` / `+58`） | `~0x1000` / `~u32("._\0\0")`（单文件 PE32+ 为 `~0`） |
| 载荷拷贝后写入 `image[info[3]]` 的双字 | `4096`（`0x1000`） |
| PE32 `EighthStage` 配置簇印记 | `0x00007679`（存在该印记的构建） |
| 64 位 Stage 5 特征标记（经典布局） | `70 6D 00 00 63 6D 00 00`（`"pm\0\0cm\0\0"`）与 `00 00 00 40 01 00 00 00` |

## 加解密与校验算法速查

| 算法原语 | 计算公式（按无符号 8 位/32 位回绕） |
| --- | --- |
| `header_kdf` | `info[i + 1] = k ^ cell; k = (i * i) ^ ((k + cell - i) & MASK32)` |
| `payload_xor_chain` | `k0 = info[0] + ~decrypt_size; out = k ^ cell; k = (i * i) ^ ((k + cell + i) & MASK32)` |
| `xor_ror_dwords`（`dd3`） | `v = x ^ key; key += i; out = ror32(v, shift) - i`（64 位：`19`/`21`；32 位：8 组移位候选集） |
| `byte_rotate3`（`dd4`） | `b = ((addr >> 8) + addr) & 0xFF; b2 = b + 1`；执行三次按位循环左移 `rol8` 3 位，依次异或 `b2` 与 `b` |
| `byte_rotate2`（`dd5`） | `b = va & 0xFF; b2 = b + 1`；执行三次按位循环左移 `rol8` 2 位，依次异或 `b2` 与 `b`（仅与当前位置相关） |
| `lfsr_keystream`（`dd6`） | 初始种子 `1`，多项式 `0x8003`，每字节 8 位、低位优先（LSB-first）；明文长度位于 `pos + 95` |
| `string_cipher`（`dd7`） | `ror8(b, 4) - key`（`0 -> -key`），`key += 67`；初始密钥为 `name_rva & 0xFF` 或 `hint_name_rva & 0xFF` |
| `page_scramble`（`dd8`，64 位） | `mixed = ror32(key, 15) + i; key = mixed + i`；对 `i >= 1` 执行 `page[i * 16 + (mixed & 0xF)] ^= key & 0xFF` |
| `page_scramble_pe32`（`dd8`，32 位） | 预步进 `key = ror32(pk, 15)`（`pk = page + 1` 或 `0x8000 * (page + 1)`），随后遍历 `i = 1..255` |
| `crc32` 与 `calculate_checksum` | 位反转多项式 CRC-32（`0xEDB88320`）；区间校验和为 `crc32(region) ^ length` |
| `advance_key` | 对 `m in 0..iterations` 依次累加 `1 .. ((m + 1) * 100)` |
| `aes_decrypt` | 全零 IV 的 AES-CBC；轮数取自 `key_offset + 2` 处的 `u16`；大端序状态字；标准 GF(2⁸) 逆 T 表 |

## PE 头部字段偏移（`pe = u32@0x3C`）

| 字段 | PE32+（`0x20B`） | PE32（`0x10B`） |
| --- | --- | --- |
| `Characteristics`（`IMAGE_FILE_DLL = 0x2000`） | `pe + 0x16` | `pe + 0x16` |
| `OptionalHeader.Magic` | `pe + 0x18` | `pe + 0x18` |
| `AddressOfEntryPoint` | `pe + 0x28` | `pe + 0x28` |
| `SizeOfImage` | `pe + 0x50` | `pe + 0x50` |
| `DllCharacteristics` | `pe + 0x5E` | `pe + 0x5E` |
| 数据目录数组起点 | `pe + 0x88`（`136`） | `pe + 0x78`（`120`） |
| 导出表目录（`DD[0]`） | `pe + 0x88` | `pe + 0x78` |
| 导入表目录（`DD[1]`） | `pe + 0x90` | `pe + 0x80` |
| 资源目录（`DD[2]`） | `pe + 0x98` | `pe + 0x88` |
| 基址重定位表（`DD[5]`） | `pe + 0xB0` | `pe + 0xA0` |
| TLS 目录（`DD[9]`） | `pe + 0xD0` | `pe + 0xC0` |
| IAT（`DD[12]`） | `pe + 0xE8` | `pe + 0xD8` |
| CLR / COM 描述符（`DD[14]`） | `pe + 0xF8` | `pe + 0xE8` |

## 按构建生成的 `AL` 字节码操作码

| 字节序列 | 汇编指令 | 解码后的操作 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | 跳过 |
| `C0 C0 ib` | `ROL AL, imm8` | `("rol", imm)` |
| `C0 C8 ib` | `ROR AL, imm8` | `("ror", imm)` |
| `FE C0` | `INC AL` | `("inc",)` |
| `FE C8` | `DEC AL` | `("dec",)` |
| `C3` | `RET` | 字节码桩结束 |

## 验证套件

上述所有变换原语均已在 [验证与参考实现](https://app.gitbook.com/s/L9bXLua8yrIPEUZOHO21/) 中通过一套独立的 Rust 移植实现完成交叉核验，覆盖 25 组具名测试样本（fixture）上的 31 项比对。在仓库根目录运行 `python verification/run_tests.py` 与 `python verification/verify_docs.py`，即可重新校验全部参考实现与文档代码块。
