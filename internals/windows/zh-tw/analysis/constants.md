---
description: "彙整特徵魔數、容器計算公式、加密演算法、PE32/PE32+ 欄位偏移與位元組碼運算碼的參考總表。"
icon: sliders
---

# 常數與偏移量

## 容器常數與特徵魔數

| 項目 | 數值 |
| --- | --- |
| 格式魔數（`info[1]`） | `0x4E4E4F4B`（小端序 ASCII 為 `KONN`） |
| 外層 PE 標頭區間／`info` 偏移量 | `4096`（`0x1000`） |
| 加密 `info` 標頭長度 | `32` 位元組（`8` 個 dword） |
| 候選檔案最小長度 | `4128`（`0x1020`）位元組 |
| `decrypt_size`（標準／完整酬載 PE32） | `info[6] - info[3] + 8192` / `info[5]`（精簡 PE32 備援值） |
| 區段資料檔案基底 | `(~u32@0x1080 + 0x1000) & 0xFFFFFFFF` |
| 伴生檔案（`._`）配對檢查 | `stub[4096..4128] == companion[0..32]` |
| 伴生檔案進入點 thunk 標記（`+53` / `+58`） | `~0x1000` / `~u32("._\0\0")`（單一檔案 PE32+ 為 `~0`） |
| 複製酬載後寫入 `image[info[3]]` 的 dword | `4096`（`0x1000`） |
| PE32 `EighthStage` 組態叢集戳記 | `0x00007679`（若存在） |
| 64 位元第 5 階段特徵標記（傳統配置） | `70 6D 00 00 63 6D 00 00`（`"pm\0\0cm\0\0"`）與 `00 00 00 40 01 00 00 00` |

## 加密演算法與檢驗和速查表

| 原語 | 計算公式（無號 8 / 32 位元溢位迴繞） |
| --- | --- |
| `header_kdf` | `info[i + 1] = k ^ cell; k = (i * i) ^ ((k + cell - i) & MASK32)` |
| `payload_xor_chain` | `k0 = info[0] + ~decrypt_size; out = k ^ cell; k = (i * i) ^ ((k + cell + i) & MASK32)` |
| `xor_ror_dwords`（`dd3`） | `v = x ^ key; key += i; out = ror32(v, shift) - i`（64 位元為 `19`/`21`；32 位元為 8 組位移集合） |
| `byte_rotate3`（`dd4`） | `b = ((addr >> 8) + addr) & 0xFF; b2 = b + 1`；`rol8` 左旋 3 位元共三次，先 XOR `b2` 再 XOR `b` |
| `byte_rotate2`（`dd5`） | `b = va & 0xFF; b2 = b + 1`；`rol8` 左旋 2 位元共三次，先 XOR `b2` 再 XOR `b`（僅與單一位址相關） |
| `lfsr_keystream`（`dd6`） | 種子 `1`、多項式 `0x8003`、每位元組 8 位元由 LSB 優先；明文長度位於 `pos + 95` |
| `string_cipher`（`dd7`） | `ror8(b, 4) - key`（`0 -> -key`），每步 `key += 67`；初始金鑰為 `name_rva & 0xFF` 或 `hint_name_rva & 0xFF` |
| `page_scramble`（`dd8`，64 位元） | `mixed = ror32(key, 15) + i; key = mixed + i`；對 `i >= 1` 執行 `page[i * 16 + (mixed & 0xF)] ^= key & 0xFF` |
| `page_scramble_pe32`（`dd8`，32 位元） | 預先推進 `key = ror32(pk, 15)`（`pk = page + 1` 或 `0x8000 * (page + 1)`），再對 `i = 1..255` 迭代 |
| `crc32` 與 `calculate_checksum` | 反向多項式 CRC-32（`0xEDB88320`）；區間檢驗和為 `crc32(region) ^ length` |
| `advance_key` | 對 `m in 0..iterations` 依序累加 `1 .. ((m + 1) * 100)` |
| `aes_decrypt` | 零 IV 之 AES-CBC；`key_offset + 2` 處 `u16` 為輪數；狀態字組採大端序；使用標準 GF(2⁸) 逆向 T-table |

## PE 標頭偏移量（`pe = u32@0x3C`）

| 欄位 | PE32+（`0x20B`） | PE32（`0x10B`） |
| --- | --- | --- |
| `Characteristics`（`IMAGE_FILE_DLL = 0x2000`） | `pe + 0x16` | `pe + 0x16` |
| `OptionalHeader.Magic` | `pe + 0x18` | `pe + 0x18` |
| `AddressOfEntryPoint` | `pe + 0x28` | `pe + 0x28` |
| `SizeOfImage` | `pe + 0x50` | `pe + 0x50` |
| `DllCharacteristics` | `pe + 0x5E` | `pe + 0x5E` |
| 資料目錄陣列起點 | `pe + 0x88`（`136`） | `pe + 0x78`（`120`） |
| 匯出表目錄（`DD[0]`） | `pe + 0x88` | `pe + 0x78` |
| 匯入表目錄（`DD[1]`） | `pe + 0x90` | `pe + 0x80` |
| 資源目錄（`DD[2]`） | `pe + 0x98` | `pe + 0x88` |
| 基底重定位表（`DD[5]`） | `pe + 0xB0` | `pe + 0xA0` |
| TLS 目錄（`DD[9]`） | `pe + 0xD0` | `pe + 0xC0` |
| IAT（`DD[12]`） | `pe + 0xE8` | `pe + 0xD8` |
| CLR / COM 描述元（`DD[14]`） | `pe + 0xF8` | `pe + 0xE8` |

## 各組建專屬 `AL` 位元組碼運算碼

| 位元組 | 組語指令 | 解碼後操作 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | 略過 |
| `C0 C0 ib` | `ROL AL, imm8` | `("rol", imm)` |
| `C0 C8 ib` | `ROR AL, imm8` | `("ror", imm)` |
| `FE C0` | `INC AL` | `("inc",)` |
| `FE C8` | `DEC AL` | `("dec",)` |
| `C3` | `RET` | stub 結束 |

## 驗證測試套件

上述每項轉換皆已透過[驗證與參考實作](https://app.gitbook.com/s/2p7kzW649ZlKfmpYdJ87/)中的 25 組具名參考 fixture、共 31 項交叉比對，與另一套獨立的 Rust 實作逐位元組核對無誤。在儲存庫根目錄執行 `python verification/run_tests.py` 與 `python verification/verify_docs.py`，即可重新驗證所有參考實作與各頁面中的程式碼區塊。
