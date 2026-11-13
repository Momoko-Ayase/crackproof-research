---
description: "Android IL2CPP 中繼資料的方法 token 與 methodIndex 置換及儲存配置。"
icon: database
---

# 中繼資料

在 Unity IL2CPP 的 Android 組建中，CrackProof 會連同 `libil2cpp.so` 一併保護 `global-metadata.dat`。依中繼資料版本與封裝方式而定，保護機制可能是置換外部 `global-metadata.dat` 檔案內的方法 token 或 `methodIndex` 欄位（執行期由模組 `0x0C` 攔截 `mmap` 即時還原），或是以 32 位元 XOR 金鑰將精簡版第 24 版中繼資料區塊封裝在 `.so` 的資料區段內。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-hashtag"></i></td><td><strong>方法 token</strong></td><td>第 29、31、39 版的五回合逆置換、第 31 版表格順序重映射備援，以及 24.1 版 <code>methodIndex</code> 復原。</td><td><a href="method-tokens.md">方法 token</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>儲存配置</strong></td><td>外部 <code>global-metadata.dat</code> 的套件配對規則，以及內嵌 XOR 封裝的精簡版 v24 中繼資料區塊。</td><td><a href="storage-layouts.md">儲存配置</a></td></tr></tbody></table>
