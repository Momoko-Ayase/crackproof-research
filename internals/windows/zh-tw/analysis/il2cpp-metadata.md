---
description: "還原 Unity IL2CPP 的 Windows -GMD 稀疏 MethodDef token 混淆。"
icon: table
---

# il2cpp 中繼資料混淆

在 Unity IL2CPP 的 Windows 組建上，CrackProof 選用的 `-GMD` 模式除了保護 PE 檔（`GameAssembly.dll`）之外，還會同步修改 `global-metadata.dat`，改寫每一筆 `Il2CppMethodDefinition` 項目的 `token` 欄位。

## 運作機制與崩潰症狀

IL2CPP 在啟動時會以 `(token & 0x00FFFFFF) - 1` 作為索引，從 `Il2CppCodeGenModule.methodPointers` 與 `invokerIndices` 陣列中查找每個方法編譯後的函式指標與呼叫器索引。由於這兩個陣列的長度正好等於該模組實際編譯的方法數量，IL2CPP 要求每個模組內的 `MethodDef` RID 必須構成 `1..=methodPointerCount` 的連續數列。

`-GMD` 會把這組連續 RID 換成稀疏的 ECMA-335 風格 token（例如某模組僅有約 `14,000` 個編譯方法，RID 卻跳到約 `55,000`）。在受保護行程內部，CrackProof 執行期會在 IL2CPP 讀取前先行重映射回連續值；若僅對 `GameAssembly.dll` 做靜態脫殼而未同步還原 `global-metadata.dat`，`il2cpp_init` 執行時就會因為 `(token_row - 1)` 超出陣列邊界而崩潰（常見症狀為初始化 `System.Array` 介面方法時觸發 `0xC0000005` 存取違規）。

## 無須金鑰的結構性還原

由於 `Il2CppMethodDefinition` 各列原本就依所屬型別（`Il2CppTypeDefinition`）連續排列，而型別又依所屬模組（`Il2CppImageDefinition`）連續排列，每個方法的標準 token 完全由資料表順序決定，不需要任何金鑰即可直接推算還原：

```text
local_index = method_index - image_first_method_index
new_token   = 0x06000000 | ((local_index + 1) & 0x00FFFFFF)
```

欄位（Field）與型別（Type）的 token 本身維持標準值，無須改動。若對未經混淆的 `global-metadata.dat` 套用上述公式，算出的 `new_token` 會與原本的 `token` 完全相同，因此這項轉換具備冪等性（Idempotent）。

## 第 31 版中繼資料配置常數

| 項目 | 數值 |
| --- | --- |
| 檔案魔數（`+0x00`） | `0xFAB11BAF` |
| 中繼資料版本（`+0x04`） | `31` |
| 標頭 `{offset, size}` 欄位對 | `methods @0x30`、`types @0xA0`、`images @0xA8` |
| 結構項目步幅（Stride） | `method = 0x24`、`type = 0x58`、`image = 0x28` |
| 關鍵欄位 | `method.token`（`+0x18` 的 `u32`）；`type.methodStart`（`+0x24` 的 `u32`）、`type.method_count`（`+0x40` 的 `u16`）；`image.typeStart`（`+0x08` 的 `u32`）、`image.typeCount`（`+0x0C` 的 `u32`） |

寫出還原後的位元組前，務必先驗證魔數 `0xFAB11BAF`、`version == 31`、各資料表未超出檔案邊界、資料表大小可被項目步幅整除，且各模組的方法區間彼此連續不重疊。至於 Android IL2CPP 組建，則是採用帶種子的五輪 RID 或 `methodIndex` 置換，由模組 `0x0C` 負責還原（在第 31 版中繼資料上亦保留 `-GMD` 作為備援模式）；詳見 [Method token 混淆](https://app.gitbook.com/s/HezwIJwx0lhm5CUG7g8R/metadata/method-tokens)。
