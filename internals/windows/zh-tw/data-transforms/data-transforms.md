---
description: "Windows 頭、加載器階段、名稱、節與代碼頁所用的可逆數據變換。"
---

# 數據變換

CrackProof 並非只使用一種覆蓋整個容器的密碼，而是疊加多個小型變換。輸入範圍、地址依賴與執行順序都很重要：即使對錯誤範圍使用了正確變換，也可能產生看似合理的字節。

各頁按用途拆分：

- [滾動密鑰與旋轉密碼](rolling-and-rotation.md)介紹早期階段與小型記錄使用的操作。
- [LFSR、字符串與頁變換](lfsr-strings-pages.md)介紹嵌入式指令流、導入名與稀疏代碼頁變化。
- [校驗和與密鑰推進](checksums.md)說明記錄驗證，以及一個結果如何推進下一個密鑰。
- [AES-CBC](aes.md)、[Huffman/LZ 壓縮](compression.md)與[按構建定製的字節變換](bytecode-transform.md)組成主要的節數據處理路徑。
