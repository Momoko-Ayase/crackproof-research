---
description: "外部 global-metadata.dat 套件配對與內嵌 XOR 精簡版 v24 中繼資料區塊。"
icon: table
---

# 儲存配置

受保護的 Android IL2CPP 組建會以下列兩種儲存形式之一隨附中繼資料：

| 變體 | 儲存位置 | 解封裝後的格式 |
| --- | --- | --- |
| 外部 `global-metadata.dat` | 位於 `assets/bin/Data/Managed/Metadata/`（或 split APK 資源套件）下的獨立檔案 | 帶有標準 `0xFAB11BAF` 檔頭的第 `24`（`v24.1`）、`29`、`31` 或 `39` 版 |
| 內嵌精簡版 + XOR 區塊 | 位於已復原 `libil2cpp.so` 映像內的 `0x2701F30` 位元組資料區塊 | 探測 dword `[0x9732CA38, 0xBAC4374F]` 改寫為 `[0xFAB11BAF, 24]` |

{% hint style="info" %}
Stage 2 的 `0x5C` 紀錄描述元內含 `metadata_offset`／`metadata_size` 欄位，但這些欄位存放的是保護器模組自身的載入、重定位與匯入中繼資料，而非 IL2CPP 的 `global-metadata.dat`。將外部 `v24.1` `global-metadata.dat` 與模組 `0x0C` 配對時，兩個檔案必須屬於同一個應用程式套件（跨 split APK 比對 `AndroidManifest.xml` 的 `package` 與 `versionCode`／`versionCodeMajor` 一致，或位於同一個 `<root>/lib/<abi>/` 與 `<root>/assets/` 資料夾結構下）。
{% endhint %}

## 內嵌精簡版 + XOR 變體

部分較早期的第 `24` 版封裝形式不會在 `assets/` 資料夾下放置 `global-metadata.dat`，而是將一段長 `0x2701F30` 位元組、經 XOR 遮罩處理的資料區塊直接內嵌在已復原 `.so` 的資料區段中：

* **結構：** 開頭為 `0x100` 位元組檔頭（64 個小端序 `u32`，每個檔頭字組各自對應一把 32 位元 XOR 金鑰），其後緊接 256 個長度不一的主體分段（每個分段各用一把 32 位元 XOR 金鑰，對分段內所有雙字組執行 XOR）。
* **檔頭探測與修補：** 將前兩個雙字組（dword）與 `[0x39184C70, 0xD901AFD4]` 執行 XOR 後，會得到位元組反序的哨兵值配對 `[0x9732CA38, 0xBAC4374F]`。依序套用 64 把檔頭金鑰與 256 把分段金鑰，再將開頭兩個雙字組改寫為 `[0xFAB11BAF, 24]`，即可產出有效的精簡版第 24 版中繼資料檔案。
* **金鑰推導現況：** 在執行期，中繼資料載入器會動態產生這 320 把 `u32` 金鑰；僅從 `.so` 二進位檔靜態推導這組金鑰流的完整路徑目前尚未追蹤完畢。同一產品線的後續新組建已改用外部 `global-metadata.dat` 檔案搭配帶種子的 `MethodDef` 置換。
