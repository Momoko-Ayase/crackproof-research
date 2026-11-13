---
description: "Stage 2 串流直譯器、ELF 與中繼資料還原及執行階段檢查的模組識別碼總表。"
icon: layer-group
---

# 執行階段模組

Stage 2 各筆記錄皆以 1 位元組的 `command_id`（`0x00`..`0xFF`）登錄模組。靜態還原僅使用 [模組串流](../restoration/module-streams.md) 所列出的模組；其餘模組則負責執行載入期檢查或輔助服務。

## 串流直譯器與啟動槽位

| ID | 用途 |
| --- | --- |
| `0xE2`..`0xE8` | 巢狀記錄串流直譯器（`0xE2` 為解密後的 Stage 2 根映像） |
| `0xF3`..`0xF8` | 作為輸入傳遞給 `0xE3`..`0xE8` 的直接切片串流（`sid = command_id - 0x10`） |
| `0xD0` | Stage 2 由 `(X6, X7)` 登錄的 `SHT_LOUSER` 檔案尾端映射 |

## 映像、符號、建構函式與中繼資料還原

| ID | 用途 |
| --- | --- |
| `0x9B` | 還原協調模組，內含 `Module9bConfig`（`header_seed`、`container_seed`、反向排列的 AES-256 回合金鑰、`skip_aes`），負責還原目標程式區段與頁面權限 |
| `0x9D` | 直接切片 payload，內含 `0x5C` 位元組的 `ProtectedDescriptor`、主 `PT_LOAD` 容器，以及輔助重定位與符號容器 |
| `0x9E` | 從外層可見 ELF 移除的隱藏 `.dynsym` 符號與 `.dynstr` 字串 |
| `0x96` | 16 位元組區塊解密模組，內含 `auxiliary_symbol_seed`，用於還原輔助重定位表被打亂的符號索引 |
| `0x98` | 最終建構函式分派模組：於映像還原完成後解析並呼叫目標程式庫的 `.init_array` 回呼函式（對應 Windows 狀態碼 `280`） |
| `0x0C` | 僅見於 IL2CPP 組建：攔截 `mmap` 以在載入時解除 `global-metadata.dat` 混淆，並內嵌 `v24.1` 的 `methodIndex` 種子與 256 筆例外表 |
| `0xB9` | 中繼資料相關輔助區塊（於 IL2CPP 組建中帶有實際內容；一般原生程式庫則不含此記錄或內容為空） |

## 環境檢查、符號查詢與完整性輔助模組

| ID | 用途 |
| --- | --- |
| `0x81` | 解密程式庫與符號名稱，透過 `dlopen` / `dlsym` 解析函式指標並加以快取 |
| `0x8F` | 讀取 `/proc/self/cmdline`、查詢 `uid`/`gid`/`tid`、管理環境 token，並檢查路徑擁有者與權限模式 |
| `0x97` | 掃描 `/proc` 中相同 UID 的行程、在寫入程式碼前後以 `mprotect` 切換頁面權限，並啟動分離式監控執行緒 |
| `0x02` | 透過 UDP 連接埠 123 發送 NTP 時間查詢，並比對回應是否超出門檻值 |
| `0x69` | `fork` 出偵測用子行程並檢查其結束狀態 |
| `0x60` | 掃描系統程式庫資料夾、`/proc` 環境變數與執行期路徑 |
| `0x40` | 驗證 `base.apk` 與 split APK 簽章（順序為 v3.1 -> v3 -> v2 -> v1/JAR） |
| `0x20` | 驗證目標檔案路徑、ELF 標頭、`/proc/self/maps` 與 `libc` 映射 |
| `0x33` | 建立 `dex2oat` 參數清單，並移除不相符的 oat/art 產物 |
| `0x72` | 開啟 Unix domain socket 並接受連線（`bind` / `listen` / `accept`） |
| `0xB0` | 轉換內部 sentinel 標記表 |

<details>
<summary>其他已觀測到的模組識別碼（未分類）</summary>

`0x8E`、`0x6A`、`0x68`、`0x54`、`0x71`、`0x53`、`0xA4`、`0x58`、`0x73`、`0xA0`、`0xB2`。

這些識別碼會與上述模組一同出現在巢狀 Stage 2 串流中，登錄至 256 格模組表，並在未設定 `flags & 0x100` 時執行 `init`/`entry` 回呼函式。靜態 ELF 還原不依賴這些模組。
</details>
