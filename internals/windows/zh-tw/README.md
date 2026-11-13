---
description: "CrackProof Windows PE 內部結構、資料轉換、分階段還原與執行期檢查。"
icon: desktop
---

# CrackProof for Windows 內部機制

CrackProof for Windows 用於保護 PE32（`0x10B`）與 PE32+（`0x20B`）執行檔及 DLL。受保護的二進位檔保留合法的外層 PE 結構供系統映射前導載入器，而原始應用程式區段、載入器各階段、匯入表與 CLR 中繼資料，以及程式碼分頁皆以加密與壓縮形式存放。載入時，執行期模組會先檢查主機環境、重建記憶體映像，並視設定透過例外處理常式保護可執行分頁，最後才將控制權移交給原始進入點（OEP）。

實測樣本涵蓋原生與受控（.NET）的 EXE 與 DLL、帶標記與無標記的 64 位元外殼、標準型與精簡型 32 位元外殼、64 位元專用 DLL 容器，以及拆分為 4 KiB 存根檔與外部 `._` 伴生檔案的 PE32+ 模組。

## 慣例說明

* 除非另有說明，所有位移皆為從檔案開頭起算的十六進位位元組位移。`u32@X` 表示位移 `X` 處的小端序 32 位元無號整數。
* **RVA**（相對虛擬位址）依循標準 PE 定義。映像重建在以 RVA 為索引的映像緩衝區上進行（64 位元輸出維持 `VirtualAddress == PointerToRawData`；32 位元輸出則依 `0x200` 檔案對齊緊縮重排）。
* 整數運算採固定寬度 8 位元或 32 位元無號溢位回繞，與 x86 指令語意一致；Python 範例透過明確位元遮罩（`& 0xFF`、`& 0xFFFFFFFF`）呈現。
* `info[0..7]` 代表從檔案位移 `0x1000` 解出的 8 個 32 位元 dword（詳見[容器結構與加密標頭](file-structure/container-layout.md)）。

## 章節導覽

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-folder-tree"></i></td><td><strong>檔案結構</strong></td><td>磁碟容器在 <code>0x1000</code> 處的切分、<code>KONN</code> 標頭金鑰衍生、組建家族與外部 <code>._</code> 伴生檔案。</td><td><a href="file-structure/file-format.md">受保護檔案結構</a></td></tr><tr><td><i class="fa-shuffle"></i></td><td><strong>資料轉換</strong></td><td>滾動 XOR 與旋轉加密、LFSR、字串與分頁擾碼、CRC 與階段金鑰、AES-CBC、Huffman/LZ 及隨組建位元組轉換。</td><td><a href="data-transforms/data-transforms.md">資料轉換</a></td></tr><tr><td><i class="fa-stairs"></i></td><td><strong>載入與區段還原</strong></td><td>64 位元九階段鏈、PE32 標準型與精簡型外殼、專用 DLL 變體，以及無標記結構探索。</td><td><a href="loading-and-pe-repair/loading/README.md">載入與區段還原</a></td></tr><tr><td><i class="fa-puzzle-piece"></i></td><td><strong>PE 重建</strong></td><td>區段標頭、暫態進入點與資料目錄區塊、匯入表與 <code>.kmiat</code>、TLS、匯出表、重定位與 CLR 覆蓋寫入。</td><td><a href="loading-and-pe-repair/pe-reconstruction/README.md">PE 重建</a></td></tr><tr><td><i class="fa-play"></i></td><td><strong>執行期機制</strong></td><td>狀態記錄、<code>AAA-BBB-CCC</code> 錯誤碼、反分析檢查、<code>KiUserExceptionDispatcher</code> 分頁保護、輔助模組與 <code>Htsysm</code> 驅動程式。</td><td><a href="runtime/runtime.md">執行期行為</a></td></tr><tr><td><i class="fa-compass"></i></td><td><strong>分析筆記</strong></td><td>靜態與動態分析流程、已知限制、<code>-GMD</code> IL2CPP 中繼資料重映射，以及位移與常數總表。</td><td><a href="analysis/analysis.md">分析筆記</a></td></tr></tbody></table>

本章節各項資料轉換的可執行 Python 實作與測試向量收錄於[驗證與參考實作](https://app.gitbook.com/s/2p7kzW649ZlKfmpYdJ87/)。其中 3 位元組 Huffman/LZ token 編碼與緩衝區內建 AES 金鑰排程亦見於 [CrackProof for Android SO 內部機制](https://app.gitbook.com/s/HezwIJwx0lhm5CUG7g8R/)。
