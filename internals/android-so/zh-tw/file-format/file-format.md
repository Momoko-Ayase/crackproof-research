---
description: "辨識受保護的 Android ELF64 程式庫，並界定 Stage 1 與 Stage 2 範圍。"
icon: folder-tree
---

# 檔案格式

受保護的 Android 共用程式庫依然是合法的小端序 ELF64 AArch64 二進位檔案。動態連結相關區段仍保留在區段標頭表中，而可載入的程式碼與資料區間則會清零，原內容移入檔案尾端單一的 `SHT_LOUSER` 私有區段。

格式驗證採嚴格標準：標頭型別、區段位移、參數邊界與巢狀串流範圍必須全數通過檢查，才判定為有效的受保護檔案。執行期載入器如何定位這些結構，請參閱 [Stage 1 啟動引導](../runtime/stage1-bootstrap.md)。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-file-code"></i></td><td><strong>受保護 ELF</strong></td><td>必備的 ELF64 標頭、動態區段、<code>.init_array</code> 啟動槽位與 APK 附屬檔案。</td><td><a href="protected-elf.md">受保護 ELF</a></td></tr><tr><td><i class="fa-box-archive"></i></td><td><strong>Stage 1 標頭</strong></td><td><code>SHT_LOUSER</code> 私有區段版面、32 位元組參數標頭與相對位移邊界。</td><td><a href="stage1.md">Stage 1 標頭</a></td></tr><tr><td><i class="fa-bars-staggered"></i></td><td><strong>Stage 2 串流</strong></td><td><code>0x5C</code> 位元組記錄描述元、直接切片與子串流判別，以及容器資料分派。</td><td><a href="stage2-streams.md">Stage 2 串流</a></td></tr></tbody></table>
