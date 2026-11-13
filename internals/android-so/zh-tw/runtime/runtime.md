---
description: "Stage 1 啟動流程、巢狀 Stage 2 直譯器與載入期環境檢查機制。"
icon: play
---

# 執行階段

載入階段由 Android 動態連結器映射被挖空的 ELF 並執行 `.init_array`，進入 Stage 1 啟動 stub。Stage 1 負責映射並解密 Stage 2（`0xE2`），由 Stage 2 配置 256 格模組表、逐層執行巢狀直譯器串流（`0xE2`..`0xE8`）、執行使用者空間的環境與完整性檢查、還原記憶體中的 ELF 程式區段與重定位項目，最後透過模組 `0x98` 呼叫原始建構函式。

靜態還原只需讀取容器、符號、重定位、建構函式與中繼資料相關紀錄（`0x9B`、`0x9D`、`0x9E`，以及選用的 `0x96`、`0x98` 與 `0x0C`）；環境檢查模組僅在執行階段運作。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-bolt"></i></td><td><strong>Stage 1 啟動流程</strong></td><td>透過 <code>/proc/self/maps</code> 定位自身檔案、解密 <code>SHT_LOUSER</code>、偵測頁面大小並移交暫存器參數。</td><td><a href="stage1-bootstrap.md">Stage 1 啟動流程</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>Stage 2 直譯器</strong></td><td>256 格模組表、<code>0x5C</code> 記錄描述元格式，以及 <code>0xE2</code>..<code>0xE8</code> 分層串流執行機制。</td><td><a href="stage2-interpreter.md">Stage 2 直譯器</a></td></tr><tr><td><i class="fa-user-shield"></i></td><td><strong>環境與完整性檢查</strong></td><td>NativeBridge 轉譯偵測、<code>PTRACE_SEIZE</code> 輔助行程、<code>/proc/&lt;pid&gt;/mem</code> 讀取監控與 APK 簽章驗證。</td><td><a href="environment-checks.md">環境與完整性檢查</a></td></tr><tr><td><i class="fa-layer-group"></i></td><td><strong>執行階段模組</strong></td><td>彙整已觀測到的 Stage 2 模組識別碼，涵蓋串流直譯器、映像還原與環境偵測模組。</td><td><a href="modules.md">執行階段模組</a></td></tr></tbody></table>
