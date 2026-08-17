---
description: 容器格式、加載器與運行時各處使用的常量、偏移與編碼速查表。
---

# 常量與偏移

## 格式 magic

| magic  | 值            | 含義  |
| ------ | ------------ | --- |
| `KONN` | `0x4E4E4F4B` | 容器戳 |

## 容器常量

| 項                           | 值                                                     |
| --------------------------- | ----------------------------------------------------- |
| 頭區大小 / info 頭偏移             | `4096`（`0x1000`）                                      |
| info 頭大小                    | 32 字節（8 個 dword）                                      |
| 最小識別長度                      | 4128 字節                                               |
| `decrypt_size`（payload 鏈長度） | `info[6] - info[3] + 8192`                            |
| 節數據文件基址                     | `(~u32@0x1080) + 0x1000`                              |
| 伴生體配對檢查                     | `stub[4096..4128] == companion[0..32]`                |
| 文件完整性 dword                 | `u32@0x38 + 0x76543211`（混淆存儲於偏移 `0x38`）               |
| 配置簇版本戳（32 位）                | `0x00007679`                                          |
| stage-5 標記（64 位標記佈局）        | `70 6D 00 00 63 6D 00 00` 與 `00 00 00 40 01 00 00 00` |

## 原語速查

| 原語               | 公式                                                                             |
| ---------------- | ------------------------------------------------------------------------------ |
| 頭部 KDF           | `info[i+1] = k ^ cell; k = i² ^ (k + cell − i)`                                |
| payload 鏈        | `out = k ^ cell; k = i² ^ (k + cell + i)`                                      |
| XOR-ROR dword 密碼 | `v = x ^ key; key += i; out = ror(v, shift) − i`（shift 19/21）                  |
| 字節 rotate-3      | 三次 `rol3`，間插 XOR `b2`、`b`；密鑰逐字節 +1                                             |
| 字節 rotate-2      | 三次 `rol2`，間插 XOR `b2`、`b`；以地址低字節為鑰                                             |
| LFSR             | 種子 1，反饋 `0x8003`，每字節 8 位 LSB 優先；塊長度在 `+95`                                     |
| 字符串密碼            | `ror4(b) − key`（0 → `−key`），`key += 67` 逐字節                                    |
| 頁擾動（64 位）        | `mixed = ror15(key)+i; key = mixed+i; page[i*16 + (mixed&0xF)] ^= key`，塊 0 只推進 |
| 頁擾動（32 位）        | 同循環，前置 `key = ror15(pk)`；`pk = page+1` 或 `0x8000*(page+1)`                     |
| CRC-32           | 反射，多項式 `0xEDB88320`                                                            |
| 校驗和描述符           | `crc32(region) ^ length`                                                       |
| 三角數調度            | 每輪 `m`：`key += 1..(m+1)*100`                                                   |
| AES              | CBC 解密；輪數為調度表+2 處 u16；狀態大端；標準逆 T 表                                             |

## PE 字段偏移

| 字段                    | PE32+                                   | PE32             |
| --------------------- | --------------------------------------- | ---------------- |
| `AddressOfEntryPoint` | `pe + 0x28`                             | `pe + 0x28`      |
| 數據目錄基址                | `pe + 0x88`（136）                        | `pe + 0x78`（120） |
| 導入目錄（DD\[1]）          | `pe + 0x90`                             | `pe + 0x80`      |
| 基址重定位（DD\[5]）         | `pe + 0xB0`                             | `pe + 0xA0`      |
| TLS（DD\[9]）           | `pe + 0xD0`                             | `pe + 0xC0`      |
| IAT（DD\[12]）          | `pe + 0xE8`                             | `pe + 0xD8`      |
| CLR/COM 描述符（DD\[14]）  | `pe + 0xF8`                             | `pe + 0xE0`      |
| `DllCharacteristics`  | `pe + 0x5E`                             | `pe + 0x5E`      |
| `SizeOfImage`         | `pe + 0x50`                             | `pe + 0x50`      |
| `IMAGE_FILE_DLL` 位    | Characteristics（`pe + 0x16`）中的 `0x2000` | 相同               |

## 字節碼 stub 操作碼錶

| 字節         | 指令             | 操作  |
| ---------- | -------------- | --- |
| `04 ib`    | `ADD AL, imm8` | add |
| `2C ib`    | `SUB AL, imm8` | sub |
| `34 ib`    | `XOR AL, imm8` | xor |
| `90`       | `NOP`          | 無   |
| `C0 /0 ib` | `ROL AL, imm8` | rol |
| `C0 /1 ib` | `ROR AL, imm8` | ror |
| `FE /0`    | `INC AL`       | inc |
| `FE /1`    | `DEC AL`       | dec |
| `C3`       | `RET`          | 結束  |

ModR/M 必須是寄存器直接尋址的 `AL`（`mod=3, rm=0`）；其餘一律無效。

## 交叉引用

* 狀態碼與啟動序列：[運行時行為](../runtime/startup-status.md#啟動序列與狀態碼)
* 模塊代碼與驅動世代：[內核驅動與子模塊](../runtime/kernel-components.md)
* il2cpp 元數據常量：[il2cpp 元數據混淆](il2cpp-metadata.md)
* Huffman 表/token 格式：[數據變換原語](../data-transforms/compression.md#huffmanlz-壓縮格式)

## 驗證套件

本文檔中的每個 Python 片段在發佈前都經過驗證：每個函數的輸出在相同輸入上與算法的獨立參考移植逐字節比對（30 個測試向量，全部一致）。完整可運行的片段文件與比對工具發佈在本站的[驗證與參考](https://app.gitbook.com/o/-Lx9XUuXVg8x3nx7ouIX/s/2p7kzW649ZlKfmpYdJ87/)欄目中——運行 `python run_tests.py` 可重跑全部比對。
