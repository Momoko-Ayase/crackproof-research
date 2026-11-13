---
description: "重建 PE 區段標頭、進入點、資料目錄、匯入表、TLS、匯出表、重定位與 CLR 結構。"
icon: puzzle-piece
---

# PE 重建

區段還原完成後，會得到一份以 RVA 索引的記憶體緩衝區（共 `SizeOfImage` 位元組）。若要將這份緩衝區轉回合法且可由系統載入的 PE 檔案，還必須針對該組建所屬的配置家族，依序還原遭清空或重導向的標頭欄位、匯入表、TLS 狀態、匯出表、基底重定位、遭打亂的 `.text` 分頁與 CLR 中繼資料。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-memory"></i></td><td><strong>標頭、區段與填零範圍</strong></td><td>以 RVA 對齊的區段標頭、32 位元檔案緊縮、暫時解密的進入點與資料目錄區塊，以及 <code>.bss</code> 填零串列。</td><td><a href="memory-image.md">標頭、區段與填零範圍</a></td></tr><tr><td><i class="fa-sitemap"></i></td><td><strong>匯入表、TLS 與匯出表</strong></td><td>各家族匯入表還原、<code>.kmiat</code> 區段重建、TLS 還原與重定位重新啟用，以及 stub 匯出表覆寫。</td><td><a href="imports-tls-exports.md">匯入表、TLS 與匯出表</a></td></tr><tr><td><i class="fa-cubes"></i></td><td><strong>重定位、分頁轉換與 CLR 資料</strong></td><td><code>/FIXED</code> 與 ASLR 重定位策略、<code>.text</code> 分頁打亂執行時機，以及精準的 CLR 中繼資料覆寫還原。</td><td><a href="relocations-managed.md">重定位、分頁轉換與 CLR 資料</a></td></tr></tbody></table>
