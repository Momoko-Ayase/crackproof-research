---
description: "如何把恢復後的內存映像重新組成結構一致的 PE 文件。"
---

# PE 重建

節恢復得到的是按 RVA 組織的內存映像。要形成可用的 PE 文件，還需要協調頭、文件偏移、數據目錄、導入、TLS 狀態、導出、重定位；託管映像還需要恢復 CLR 結構。

- [頭、節與零填充範圍](memory-image.md)
- [導入、TLS 與導出](imports-tls-exports.md)
- [重定位、頁變換與 CLR 數據](relocations-managed.md)

這些步驟依賴具體佈局。舊版固定基址可執行文件、需要重定基址的 DLL、外置伴生映像與 CLR 映像不能使用同一種數據目錄處理策略。
