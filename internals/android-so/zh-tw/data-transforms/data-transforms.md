---
description: "Android 串流的 GF(2^32) 運算、模組種子、金鑰展開表、容器解碼與壓縮機制。"
icon: shuffle
---

# 資料轉換

解密流程依序經過四層轉換：Stage 1 的 32 位元字組加解密、Stage 2 以 GF(2³²) 混洗的串流標頭與記錄描述元、容器內各分段的滾動字組加解密與選用 AES-256-CBC 解密，以及 Huffman/LZ 解壓縮。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-rotate"></i></td><td><strong>字組、串流與記錄加解密</strong></td><td>GF(2³²) 固定常數乘法、Stage 1 字組加解密、串流標頭、<code>0x5C</code> 記錄描述元與 <code>0x9D</code> 描述元。</td><td><a href="word-and-record.md">字組、串流與記錄加解密</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>模組設定</strong></td><td>金鑰展開表標記 <code>00 01 0e 00</code>、AES-256 金鑰還原，以及模組 <code>0x9B</code> 與內嵌 Stage 2 的種子版面差異。</td><td><a href="module-config.md">模組設定</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>容器轉換</strong></td><td>容器標頭、分段滾動加解密、分段寫入記錄，以及輔助 ELF 容器。</td><td><a href="container.md">容器轉換</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>Huffman 與 LZ 壓縮</strong></td><td>3 位元組 Huffman 樹森林、16 位元前綴查詢表、四種編碼模式與位元／位元組精確消耗檢查。</td><td><a href="compression.md">Huffman 與 LZ 壓縮</a></td></tr></tbody></table>
