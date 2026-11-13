---
description: "磁碟容器佈局、KONN 標頭辨識、組建家族分類與外部伴生檔案拆分。"
icon: folder-tree
---

# 受保護檔案結構

受保護的 Windows 二進位檔在前 `0x1000` 位元組保留可載入的外層 PE 標頭，將加密參數標頭置於 `0x1000`，並把分階段載入器與壓縮後的應用程式區段存放於其後（或拆分至同資料夾下的 `._` 伴生檔案）。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-box-archive"></i></td><td><strong>容器結構與加密標頭</strong></td><td>固定於 <code>0x1000</code> 的容器切分、8 個 dword 的 <code>info</code> 標頭金鑰衍生與負載搬移範圍。</td><td><a href="container-layout.md">容器結構與加密標頭</a></td></tr><tr><td><i class="fa-fingerprint"></i></td><td><strong>格式辨識與組建家族</strong></td><td>基於檔案內容的 <code>KONN</code> 偵測、PE32 與 PE32+ CLR 模組分類，以及各類容器版型。</td><td><a href="recognition.md">格式辨識與組建家族</a></td></tr><tr><td><i class="fa-copy"></i></td><td><strong>區段資料與伴生檔案</strong></td><td><code>0x1080</code> 處以位元反相編碼的區段資料基底，以及外部 <code>._</code> 伴生檔案配對與覆蓋寫入。</td><td><a href="companion-layout.md">區段資料與伴生檔案</a></td></tr></tbody></table>
