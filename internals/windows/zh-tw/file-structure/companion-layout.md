---
description: 如何定位節載荷，以及 stub 可執行文件如何引用外置伴生文件。
---

# 節數據與伴生文件

## 在文件中定位節數據

加載器表內的節內容描述符存儲的偏移，相對於一個本身以補碼編碼在文件偏移 `0x1080` 處的基址：

```
section_data_file_base = (~u32@0x1080) + 0x1000      (32-bit wrapping)
```

因此描述符的 `src` 字段映射到文件偏移 `src + section_data_file_base`。同一公式出現在所有構建家族中（在加載器代碼裡既稱 `rebase` 又稱 `compress_data_offset`）。

## 外置伴生體佈局（`._` 文件）

某些構建——目前僅在 il2cpp 作品上觀察到——把受保護模塊拆成一對文件：

* **`Foo.dll`**——磁盤上的瘦**加載器 stub**。其代碼節被裁剪到只剩一頁（即 CrackProof 加載器本體），但其頭部與 `.rdata` 是完整明文。
* **`Foo.dll._`**——全加密的**伴生體**，持有真正的 payload。它不含任何明文 PE 結構（熵 ≈ 8 比特/字節）。

伴生體逐字節等於 stub 自 CrackProof 頭部（偏移 4096）起的 payload 區。運行時加載器映射 `Foo.dll._` 並對其執行常規解包；實際運行的模塊實際上就是拼接體 `stub[..4096] ++ companion`。

配對關係由 32 字節精確匹配確認：`stub[4096..4128] == companion[0..32]`。這 32 字節覆蓋加密 info 頭（密鑰表與 magic），因此匹配即證明該伴生體就是此 stub 的 payload，而非無關文件。

stub 以明文保留的內容對後續重建很重要：

* **導出目錄**（伴生體在此處解密為密文；加載器運行時從 stub 的副本重建導出）。
* **TLS 目錄**——`IMAGE_TLS_DIRECTORY` 結構體、其原始數據模板與數據目錄項，這些都被保護層從加密 payload 中剝離（見 [PE 重建](../loading-and-pe-repair/pe-reconstruction/)）。
* 真實的 `DllCharacteristics` 字段與基址重定位表——伴生模塊**不是** `/FIXED`，與較舊的單文件構建不同。

關於此文件對在啟動時如何加載，見[運行時行為](../runtime/runtime.md)；關於缺失部分如何被還原進重建映像，見 [PE 重建](../loading-and-pe-repair/pe-reconstruction/)。
