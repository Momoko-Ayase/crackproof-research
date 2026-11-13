---
description: "標準與精簡型 PE32 外殼、64 位元專用 DLL 與無標記 64 位元組建的結構差異。"
icon: code-branch
---

# PE32、專用 DLL 與無標記版型

{% tabs %}
{% tab title="PE32（標準型與精簡型）" %}
32 位元（`0x10B`）容器執行八階段鏈（`SecondStage` 至 `EighthStage`），各階段內部指標皆帶有一組隨組建變動的階段大小偏移量 `ss_shift`。實測組建包含兩種 `tbl` 版型（較早期的精簡型外殼另可能在 `payload_xor_chain` 中加密整段 `info[5]` 負載）：

| 結構／位移 | 標準型 PE32（`match - 0x88`） | 精簡型 PE32（`match - 0x78`） |
| --- | --- | --- |
| `tbl` 內的 `info[6]` 比對位址 | `tbl + 0x88` | `tbl + 0x78` |
| 標頭校驗和描述子陣列 | `tbl + 0x58` | `tbl + 0x50` |
| `SecondStage` `(offset, size)` | `tbl + 0x98` | `tbl + 0x88` |
| `first_stage_cs` / `second_stage_cs` | `tbl + 0xA8` / `tbl + 0xB0` | `tbl + 0x98` / `tbl + 0xA0` |
| 備份匯入表 RVA | `tbl + 0xBC` | `tbl + 0xAC` |
| 備份資源目錄 `(RVA, size)` | `tbl + 0xC8` / `tbl + 0xCC` | `tbl + 0xB0` / `tbl + 0xB4` |
| 隨組建階段偏移量 `ss_shift` | `ss_size - 0xBC0` | `ss_size - 0xAEC` |
| `SevenStage` 種子（`seven_key`） | `~u32@(cs1_addr + cs1_size - 0x10)` | `~u32@(cs1_addr + cs1_size - 0x0C)` |

精簡型 PE32 同時將 `SecondStage` 內部指標調整為 `third_pair_off = 0xAB4 + ss_shift`，以及 `forth_key_off / third_key_off / cs_base_off / dp_base_off = 0x94C / 0x950 / 0x954 / 0x9C4 + ss_shift`。

* **標頭校驗和與 DLL `BaseReloc` 雙重測試：** `header_checksum` 會對加殼前的 PE 標頭區間逐一計算 `calculate_checksum` 並做 XOR。由於原生 PE32 DLL 的 `DD[5]`（`BaseReloc`）是由加殼器事後填入（加殼前標頭為零），還原時會同時測試「保留原標頭」與「將 `DD[5]` 清零的副本」，並採用能通過 `ThirdStage` 驗證的那一組。
* **`ThirdStage` 旋轉位數暴力測試：** 依序嘗試 `[19, 21, 17, 23, 15, 25, 13, 11]`，直到出現資訊表特徵（`1`/`0x11` 後緊接 `2`，且位址落在映像範圍內）；四組 `key_offsets` 位於其前方 `0x58` 位元組處。
* **動態 `advance_key` 輪數（`Fourth` / `Fifth` / `Seventh` / `Eighth`）：** PE32 不採用固定輪數，而是檢查 `dp_base` 與 `dp_base + 0x80` 處的四槽位表，統計開頭連續有效的 16 位元組輔助描述子數量（條件為 `size > 4`，遇到第一個空槽位即停止）。
* **`EighthStage` 金鑰與設定叢集探索：** 透過區間間隙推算與非可列印 dword 掃描取得 `EighthStage` 種子候選項，並以能否完整通過 Huffman 解壓縮作為驗證條件。在 `EighthStage` 內部，設定叢集將匯入表置於 `+0x18`、`fileCS` 置於 `+0x30`、區段描述子置於 `+0x40`、清零範圍置於 `+0x48`（若存在標記戳 `0x00007679` 則以其定位；無標記戳組建則依緊接在 `info[3]` 後方的 `fileCS` 指標結構定位）。位元組碼存根 2 會透過試解壓縮第一個壓縮區段區塊驗證，最終輸出則將 RVA 緩衝區依 `0x200` 檔案對齊緊縮重排。
{% endtab %}

{% tab title="64 位元專用 DLL" %}
較早期的 64 位元專用 DLL（僅限 `0x20B`）省略錨點掃描，直接將設定區塊置於固定位移 `anchor = info[6] + 5592`（`0x15D8`）：

| 相對 `anchor` 的位移 | 內容 |
| --- | --- |
| `+4` / `+8` | 匯入目錄大小／RVA |
| `+20` | 主階段描述子金鑰 |
| `+40` / `+44` | 資源目錄 RVA／大小 |
| `+48` / `+56` | `checksum2` / `checksum1` 描述子 |
| `+120` | 主階段描述子（右旋位數 `21`） |
| `+184` | `xor_acc` 校驗和描述子陣列 |

從主表（`addr1`）起算，次表位於 `+3632`（右旋位數 `19`，金鑰在 `+3444`），重定位／複製區塊位於 `+9248`，四組 `key_offsets` 位於 `+9160`，程式碼區塊 1..4 分別位於 `+3712 / +3728 / +3760 / +3840`，位元組碼存根 1 位於 `addr4 + 3200`，`metadata` 位於 `addr5 + 12312`，位元組碼存根 2 位於 `metadata + 88`（即 `addr5 + 12400`），區段描述子陣列則位於 `addr5 + 11976`。

* **區段描述子：** 結構為 `{dest, size, src, decompressed_size}`，搭配 `section_image_base = 4095 - u32@0x1080`；當 `size != decompressed_size` 時執行解壓縮。
* **656 位元組標頭中繼資料（`info[3] + 16`）：** 以 `byte_rotate2` 解密；`EntryPoint` 位於 `+0x10`，128 位元組的資料目錄陣列位於 `+0x20`（分別寫回 `pe + 40` 與 `pe + 136`）。
* **受控 DLL 預先填回：** 在區段區塊覆寫 IL 方法本體之前，此家族的受控組建會先從受保護原檔將承載 CLR 的區段預先填回緩衝區，事後再重新寫回 `COR20` 標頭。
{% endtab %}

{% tab title="無標記 64 位元" %}
近期 64 位元 EXE 與 DLL 外殼在 Stage 5 中同時省略了 `"pm\0\0cm\0\0"` 與 `0x40000000, 1` 標記：

1. **1 位元組步進 LFSR 掃描：** 掃描整個 Stage 5 收集所有合法的 96 位元組位元組碼存根；每次命中後仍維持 `+1` 位元組步進，避免緊鄰在真實存根前方的巧合合法片段導致掃描直接跨過真實存根。
2. **`fileCS` 鄰近度排序：** 檢查每個候選存根的 `block - 0x58`（`fileCS`），依高於 `info[3]` 的正向 RVA 差值由小到大排序測試。
3. **描述子表探測：** 以不改動原緩衝區的 `trial_byte_rotate2` 掃描候選存根附近的指標槽位，直到目標位址解析出合法的 `{src, src_len, dst, plain_len}` 區段描述子陣列。
4. **壓縮區塊實測驗證：** 對第一個壓縮區段區塊完整重播「複製 -> AES -> 存根轉換 -> `decompress`」，通過後才採納該組存根與描述子表配對。

無標記組建省略了 `walk3`；匯入表不再經由 `walk5`，而是等 `.text` 分頁擾碼還原後直接從 `DD[1]`（`IMAGE_IMPORT_DESCRIPTOR` 陣列）解密；暫態進入點與資料目錄區塊採用中繼資料版型 B（Metadata Layout B）；保留 ASLR 旗標與 `DD[5]` 重定位表；且會在 `.text` 的 `dd8` 擾碼還原完成後才寫回 CLR 中繼資料，避免位於 `.text` 內的明文 CLR 資料表遭擾碼破壞。
{% endtab %}
{% endtabs %}
