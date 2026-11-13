---
description: "執行期啟動流程、狀態碼、反分析檢查、隨選分頁保護、輔助模組與 Htsysm 驅動。"
icon: play
---

# 執行期行為

受保護的 Windows 二進位檔啟動時，會先進入 CrackProof 的引導載入器，最後才跳轉至原始進入點（`280`）。載入器會視條件開啟除錯記錄、在記憶體中手動映射輔助 DLL、檢查作業系統、虛擬機器、除錯器與行程環境、依組態初始化 `Htsysm` 核心驅動程式、重建區段與匯入表，並可選擇掛上 `KiUserExceptionDispatcher` hook 將可執行分頁重新加密保護。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-ol"></i></td><td><strong>啟動流程與狀態回報</strong></td><td>12 位元啟動狀態碼、<code>%temp%</code> 12 位十六進位資料夾開關、<code>ErrLog-Pec</code> mailslot 與 <code>AAA-BBB-CCC</code> 失敗碼。</td><td><a href="startup-status.md">啟動流程與狀態回報</a></td></tr><tr><td><i class="fa-user-shield"></i></td><td><strong>環境檢查與反分析機制</strong></td><td>除錯器、VM、開機選項、注入 DLL 與執行緒、<code>A11</code>/<code>A15</code> 宿主驗證，以及系統 DLL 反 hook 檢查。</td><td><a href="environment-checks.md">環境檢查與反分析機制</a></td></tr><tr><td><i class="fa-lock"></i></td><td><strong>分頁保護與載入器程式碼</strong></td><td><code>KiUserExceptionDispatcher</code> 隨選分頁解密、scribble 遮蔽、多態花指令、SEH 陷阱與磁碟自我映射。</td><td><a href="page-protection.md">分頁保護與載入器程式碼</a></td></tr><tr><td><i class="fa-layer-group"></i></td><td><strong>手動映射輔助模組</strong></td><td>內嵌輔助模組分工（<code>it</code>、<code>dt</code>、<code>cm</code>、<code>dm</code>、<code>sk</code>、<code>pm</code>）及其不寫入 PEB 模組串列的原因。</td><td><a href="mapped-modules.md">手動映射輔助模組</a></td></tr><tr><td><i class="fa-gears"></i></td><td><strong>Htsysm 核心元件</strong></td><td>第 1 至第 3 代核心驅動架構（<code>Htsysm</code>、<code>Htsysm7679</code>，以及含 <code>Htsysm1B4001</code> 在內的 <code>0xAA02</code> <code>ObRegisterCallbacks</code> 驅動）。</td><td><a href="kernel-components.md">Htsysm 核心元件</a></td></tr></tbody></table>
