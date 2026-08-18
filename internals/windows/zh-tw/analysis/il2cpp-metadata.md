---
description: "面向 Unity il2cpp 作品的可選 -GMD 方法令牌混淆。"
---

# il2cpp 元數據混淆

獨立於 PE 保護之外，CrackProof 提供一個選項（`-GMD`）來混淆 Unity il2cpp 作品的 **`global-metadata.dat`**。它只改變一樣東西：每條 `Il2CppMethodDefinition` 記錄的**方法令牌字段**。

## 它做了什麼，以及為什麼有效

il2cpp 解析方法的編譯函數與調用器時，用 `(token_row - 1)` 索引每個模塊的 `Il2CppCodeGenModule.methodPointers` / `invokerIndices` 表——這些表按模塊的*已編譯*方法數定長。這種索引只有當每個模塊的方法令牌是**連續**區間 `1..=methodPointerCount` 時才成立。

`-GMD` 把連續令牌換成稀疏的、原生 .NET 元數據風格的值（在一部已觀察作品中，核心庫的行號達到約 55,000，而已編譯方法只有約 14,000 個）。運行中的受保護遊戲由加載器在加載時把它們映射回去，所以遊戲能玩——但元數據文件單拎出來，就與 il2cpp 運行時的期望不一致了。

只要在受保護加載器之外消費這份元數據，問題就會顯現：脫離加載器重映射啟動的 il2cpp 映像按原值讀令牌，`(token_row - 1)` 越過每模塊表的末尾，進程在 il2cpp 初始化深處崩潰（首個受害者通常是 `System.Array` 的接口方法建立，表現為 `0xC0000005`）。解析 `global-metadata.dat` 的分析工具會看到指向編譯表中不存在行的方法引用。

## 僅憑結構即可逆轉

這種混淆不需要密鑰，也不攜帶秘密——這意味著它可以從元數據自身的結構逆轉。方法按類型分組佈局，類型按映像（模塊）分組，因此一個方法正確的令牌行號，就是它在其所屬模塊方法區間內的位置：

```
local_index = method_index - module_first_method_index
new_token   = 0x06000000 | ((local_index + 1) & 0x00FFFFFF)
```

只有方法令牌需要處理：字段令牌本就連續，類型令牌能正確解析。該變換是**冪等的**——在未混淆的元數據上，算出的令牌本就等於存儲值，應用它等於無操作。

關鍵格式常量（元數據版本 31，Unity 2022.3 時代）：

| 項 | 值 |
| --- | --- |
| sanity 魔數（偏移 0） | `0xFAB11BAF` |
| 格式版本（偏移 4） | `31` |
| 頭部表（offset/size i32 對） | methods `@0x30`、types `@0xA0`、images `@0xA8` |
| 結構步長 | method `0x24`、type `0x58`、image `0x28` |
| 字段 | method `.token +0x18`；type `.methodStart +0x24`、`.method_count +0x40`（u16）；image `.typeStart +0x08`、`.typeCount +0x0C` |

其他元數據版本使用不同的結構步長，必須按版本處理；把版本 31 的佈局套到未知版本上會損壞文件，因此任何實現都應在寫入任何一字節之前驗證魔數、版本與各表對步長的整除性。

Android 原生庫家族也會改方法令牌，但不是這種無密鑰重映射。那條路徑是帶種子的五輪置換，由模塊 `0x0C` 在 `mmap` 時還原。見[方法令牌](https://app.gitbook.com/s/HezwIJwx0lhm5CUG7g8R/metadata/method-tokens)。
