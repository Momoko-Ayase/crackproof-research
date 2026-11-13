---
description: "已觀測的 Android ELF64、加密、Stage 2 模組、重定位與 IL2CPP 中繼資料常數。"
icon: sliders
---

# 格式常數

下表彙整在已分析的 CrackProof Android AArch64 組建中觀測到的格式常數。實際判定與還原時，結構邊界與跨表一致性檢查優先於單一常數比對。

## ELF 與 Stage 1

| 常數 | 適用範圍與說明 |
| --- | --- |
| ELF64、little-endian、`EM_AARCH64`（`183` / `0xB7`） | 必要的檔案類別、位元組序與處理器架構（`e_phentsize = 0x38`、`e_shentsize = 0x40`） |
| `SHT_LOUSER`（`0x80000000`） | 位於檔案內 `PT_LOAD` 結尾 16 位元組對齊處的單一尾端私有區段 |
| `0x84` 位元組（`15 × STP` .. `15 × LDP; RET`） | 由 `.init_array` 參照的 Stage 1 啟動暫存器保存包裝常式 |
| `0x23C`（572） | 已觀測到的 Stage 1 外層包裝大小（`outer_size`） |
| `0x1000` / `0x20` | Stage 1 參數區大小 / 8 個 dword 的 Stage 1 字組標頭大小 |
| `0xBF20165D`、`0xBF189BDD` | 已觀測到的 Stage 1 字組加密常數 `C`（依組建系列區分） |
| `lib__XXXX__.so`、`assets/<id>/data1.dat` | 隨附的保護器前導 stub 共用程式庫，以及各程式庫專屬的設定資料檔 |

## 加密演算法、容器與 Stage 2 串流

| 常數 | 適用範圍與說明 |
| --- | --- |
| `0x94511DD2` / `0x579357EB` | `gf32_mul_fixed` 使用的 GF(2³²) 固定乘數 / 約化多項式 |
| `00 01 0e 00` | `Module9bConfig` 金鑰排程標記（旗標 `0x0100`、14 回合 AES-256、共 `0xF0` 位元組回合金鑰） |
| `0xE2` | Stage 2 根直譯器串流識別碼 |
| `0xE3`..`0xE8` / `0xF3`..`0xF8` | 巢狀直譯器模組及其對應的直接切片輸入串流（`sid = command_id - 0x10`） |
| `0xD0` | Stage 2 進入時登錄的 `SHT_LOUSER` 檔案尾端映射槽位 |
| `0x1800` / `0x18` | Stage 2 執行階段模組表總大小 / 單一槽位大小（共 256 格） |
| `0x5C`（23 個 dword） | Stage 2 記錄描述元與 `0x9D` `ProtectedDescriptor` 的位元組大小 |
| `0x2` / `0x100` | 描述元 `DIRECT_FLAG`（原始直接切片）/ 略過 `init` 與 `entry` 回呼函式的旗標 |
| `0x1B00` | `ContainerHeader` 中 Huffman 表（`tree_size`）的位元組長度上限 |

## 靜態還原與 IL2CPP 中繼資料

| 常數 | 適用範圍與說明 |
| --- | --- |
| `0x9B`、`0x9D`、`0x9E` | 必要的基本 ELF 還原模組（解密設定、主容器與輔助 ELF 容器、隱藏符號） |
| `0x96`、`0x98`、`0x0C` | 選用的靜態還原模組（輔助符號種子、`.init_array` 建構函式復原直譯器、`v24.1` 中繼資料種子與例外表） |
| `0x403`、`0x101`、`0x401`、`0x402` | 輔助 AArch64 重定位型別：`RELATIVE`、`ABS64`、`GLOB_DAT`（`relocation1`）與 `JUMP_SLOT`（`relocation2`） |
| `0xD65F03C0`（`RET`） | 執行 `0x98` 建構函式復原時會一併剔除的 `.init_array` 占位目標指令 |
| `0xFAB11BAF`、版本 `24`（`v24.1`）、`29`、`31`、`39` | 已觀測到的外部 IL2CPP 中繼資料魔術數值與格式版本 |
| `0xA6FAE968` | 於模組 `0x0C` 觀測到的預設 MethodDef 置換種子 |
| `0x2701F30`、`[0x9732CA38, 0xBAC4374F]` | 內嵌 XOR 封裝精簡版 v24 中繼資料的固定大小，以及解除 XOR 後的位元組反序檔頭探測 dword |
