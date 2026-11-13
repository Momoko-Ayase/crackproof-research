---
description: "Windows 版可逆加密、校驗和、AES 排程、Huffman/LZ 與位元組碼虛擬機總覽。"
icon: shuffle
---

# 資料轉換

CrackProof 在標頭、階段描述子、匯入字串、區段負載與可執行程式碼分頁上，疊加了位元組與 dword 加密、CRC-32 金鑰衍生、AES-CBC、Huffman/LZ 壓縮，以及隨組建生成的位元組置換。本章節各頁皆搭配可執行的 Python 參考程式碼，完整定義位元層級的運算細節。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-rotate"></i></td><td><strong>滾動金鑰與旋轉加密</strong></td><td><code>payload_xor_chain</code>、<code>xor_ror_dwords</code>，以及以描述子或位址衍生金鑰的三重位元組旋轉加密。</td><td><a href="rolling-and-rotation.md">滾動金鑰與旋轉加密</a></td></tr><tr><td><i class="fa-wave-square"></i></td><td><strong>LFSR、字串與分頁轉換</strong></td><td><code>0x8003</code> LFSR 存根加密、以 RVA 衍生金鑰的匯入名稱字串加密，以及逐頁 <code>.text</code> 擾碼。</td><td><a href="lfsr-strings-pages.md">LFSR、字串與分頁轉換</a></td></tr><tr><td><i class="fa-hashtag"></i></td><td><strong>校驗和與金鑰推進</strong></td><td>反射式 CRC-32、旋轉 dword 校驗和，以及三角級數多輪金鑰推進。</td><td><a href="checksums.md">校驗和與金鑰推進</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>AES-CBC 加密層</strong></td><td>搭配緩衝區內建金鑰排程與旋轉末輪 S-box 查表的全零 IV AES-CBC 解密。</td><td><a href="aes.md">AES-CBC 加密層</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>Huffman 與 LZ 壓縮</strong></td><td>每節點 3 位元組的 Huffman 樹項目，以及字面值、累加器、重複填值與 LZ 四種 token 模式。</td><td><a href="compression.md">Huffman 與 LZ 壓縮</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>隨組建生成的位元組轉換</strong></td><td>針對區段負載的九指令 <code>AL</code> x86 位元組碼直譯器與 256 位元組查表。</td><td><a href="bytecode-transform.md">隨組建生成的位元組轉換</a></td></tr></tbody></table>
