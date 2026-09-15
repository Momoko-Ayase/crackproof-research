---
description: "Android 記錄流使用的算術、模塊、容器和壓縮層。"
---

# 數據變換

Android 格式把外層首部的算術變換與容器記錄的模塊變換組合起來。壓縮是獨立的一層，必須同時校驗輸入消耗量和輸出長度。

- [詞、流與記錄密碼](word-and-record.md) 覆蓋 GF(2³²) 混合以及流/記錄頭。
- [模塊配置](module-config.md) 是 `0x9B` 的種子與 AES 材料。
- [容器變換](container.md) 展開 `0x9D` 段。
- [Huffman 與 LZ 壓縮](compression.md) 是 writer 格式，與 Windows 家族共享。

本組只描述可觀察字段和公式，不為格式中沒有出現的中間狀態另造名稱。
