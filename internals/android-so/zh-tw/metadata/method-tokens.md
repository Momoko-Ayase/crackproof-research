---
description: "復原帶種子的五回合 MethodDef RID 置換與 v24.1 methodIndex 表。"
icon: hashtag
---

# 方法 token

標準的 IL2CPP 中繼資料檔案開頭為驗證魔術數字 `0xFAB11BAF`，緊接著一個 32 位元版本號。在 Android 平台上，CrackProof 針對第 `29`、`31`、`39` 版中各映像（Image）內的 `MethodDef` RID（`0x06000000 | rid`），以及第 `24` 版（`v24.1`）的全域 `methodIndex` 項目（搭配 256 項例外表），套用帶種子的五回合鏡射減法置換。部分第 `31` 版組建則改用無金鑰的 `-GMD` token 配置。

若要與 Windows 平台的無金鑰 `-GMD` 重映射機制（僅依表格順序便能將稀疏 token 還原為 `0x06000000 | (local_index + 1)`）對照，請參閱 [il2cpp 中繼資料混淆](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/analysis/il2cpp-metadata)。

## 五回合逆運算

給定連續 `count` 個項目（`count >= 2`）與 32 位元 `seed`，先計算 `key = (seed % (count // 2)) + (count // 4)` 與 `mirror = count * 2 - 1`。每個從 0 起算的相對值 `value`（`0 <= value < count`）皆透過五個相同的回合，以 32 位元無號數溢位迴繞（`MASK32 = 0xFFFFFFFF`）進行逆運算：

```text
repeat 5 times:
    if value & 1:
        value = mirror - value
    value >>= 1
    if value >= count:
        value = mirror - value
    value = (value - key) & MASK32
    if value > count:
        value = (value + count) & MASK32
```

對於第 `29`、`31`、`39` 版的 `MethodDef` token，在各映像的閉區間 RID 範圍 `[low, high]` 內取 `value = rid - low`，還原後的 token 即為 `0x06000000 | (value + low)`。由於未混淆的標準中繼資料在每個映像內原本就具備連續的 `1..=count` RID，復原流程會先檢查該映像是否已符合標準順序，避免改動原本就乾淨的輸入檔案。

## 各版本結構配置與種子推導

{% tabs %}
{% tab title="第 29 與 31 版" %}
第 `29` 與 `31` 版使用固定的檔頭 `{offset, size}` 配對，並共用相同的型別（Type）與映像（Image）描述元結構：

* **型別表（`@0xA0`，跨距 `0x58`）：** `methodStart`（`+0x24` 處的 `u32`）、`method_count`（`+0x40` 處的 `u16`）。
* **映像表（`@0xA8`，跨距 `0x28`）：** `typeStart`（`+0x08` 處的 `u32`）、`typeCount`（`+0x0C` 處的 `u32`）。
* **方法表（`@0x30`）：**
  * **第 29 版：** 跨距 `0x20`，`token`（`u32`）位於 `+0x14`。
  * **第 31 版：** 跨距 `0x24`，`token`（`u32`）位於 `+0x18`。

在執行期，模組 `0x0C` 會攔截 `mmap` 並套用內嵌的種子（在已觀察到的預設組建中為 `0xA6FAE968`）。但在靜態復原第 `29`、`31`、`39` 版時並不需要 `0x0C`：每個映像僅有 `count / 2` 種可能的 `key` 餘數，只要逐一測試候選值能否還原出連續的 `1..=count` 標準順序，再對所有映像求取 `seed % (count / 2)` 同餘條件的交集，即可直接從 `global-metadata.dat` 推導出有效種子。若檔案本身無足夠條件約束種子，則預設採用 `0xA6FAE968`；而採用 `-GMD` 保護的第 `31` 版組建，則改依表格順序以 `0x06000000 | (local_index + 1)` 重映射。
{% endtab %}

{% tab title="第 39 版（精簡目錄）" %}
第 `39` 版以每項 12 位元組 `{offset, size, count}` 區段描述元組成的精簡目錄，取代固定的檔頭位移，並改用可變寬度的表格索引：

* `type_definition`、`parameter` 與 `generic_container` 索引的寬度依項目數而定：`1` 位元組（`count <= 255`）、`2` 位元組（`count <= 65535`）或 `4` 位元組（`count > 65535`）。
* `type_index` 的寬度由第 `18` 個區段（`interface_offsets`）推算：`count == 0` 時為 `4` 位元組，否則為 `(size / count) - 4`。

由這四個索引寬度算出方法、型別與映像紀錄的跨距及欄位位移後，後續的逐映像餘數搜尋與五回合 RID 逆運算流程皆完全相同。
{% endtab %}

{% tab title="第 24.1 版（methodIndex + 0x0C）" %}
符合 `v24.1` `Il2CppMethodDefinition` 配置（跨距 `0x34`，有號數 `i32` `methodIndex` 位於 `+0x14`）的外部第 `24` 版中繼資料不會改動 `MethodDef` token，而是置換所有非負的 `methodIndex` 項目（範圍 `0..active_count`，且 `active_count > 256`）：

1. 所有 `active_count` 個非負 `methodIndex` 槽位皆以 `key = (seed % (active_count // 2)) + (active_count // 4)` 套用五回合置換函式。
2. 前 256 個有效槽位的原始值另外儲存在模組 `0x0C` 內含 256 個項目的 `u32` 例外表。

因此，靜態復原必須將中繼資料檔案與同一應用程式解碼出的模組 `0x0C` 配對，在 `0x0C` 內定位 `{u32 seed, u32 24}` 與 `{u32 1, u32 active_count - 1}` 標頭標記及 256 項例外表，先還原這 256 筆例外項目，再對全部 `active_count` 個有效方法執行五回合逆置換。
{% endtab %}
{% endtabs %}

## 復原後驗證

重映射完成後，驗證步驟會確認映像表、型別表與方法表皆未超出檔案邊界、每個方法皆依連續表格順序隸屬於唯一一個映像、所有 `MethodDef` token 皆帶有 `0x06000000` 表格前綴且具備標準的區域 RID 順序（或在 `v24.1` 上完整涵蓋 `0..active_count`），並且不存在任何越界或重複項目。
