---
description: "擷取 Stage 2 模組資料、重建動態連結表，並輸出乾淨的 ELF64 共用程式庫。"
icon: puzzle-piece
---

# 靜態還原

靜態還原分為兩個階段：先從 `SHT_LOUSER` 擷取 Stage 2 模組資料，再據此重建 `PT_LOAD` 載入區段、動態連結表與區段標頭表並驗證輸出檔案。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-route"></i></td><td><strong>模組串流</strong></td><td>必備基礎模組（<code>0x9B</code>、<code>0x9D</code>、<code>0x9E</code>）與選用靜態模組（<code>0x96</code>、<code>0x98</code>、<code>0x0C</code>）。</td><td><a href="module-streams.md">模組串流</a></td></tr><tr><td><i class="fa-link"></i></td><td><strong>動態連結</strong></td><td>隱藏符號還原、<code>0x96</code> 符號逆置換、省略的 <code>libc</code> PLT 槽位、建構函式還原與 <code>PT_LOAD</code> 配置。</td><td><a href="dynamic-linking.md">動態連結</a></td></tr><tr><td><i class="fa-file-export"></i></td><td><strong>ELF 輸出</strong></td><td>移除 <code>SHT_LOUSER</code>、歸零 <code>e_entry</code>、搬移非載入區段，以及必要驗證與結構診斷。</td><td><a href="elf-output.md">ELF 輸出</a></td></tr></tbody></table>
