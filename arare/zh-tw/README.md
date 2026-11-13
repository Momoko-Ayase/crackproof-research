---
description: "從原始碼建置、重現已知 CrackProof 版面家族的 Windows PE 保護器。"
icon: shield-halved
---

# Arare

Arare 是從原始碼完整建置的 Windows PE 保護器，自行編譯原生與 Managed 載入器，並在每次封裝保護時即時產生專屬金鑰、AES 金鑰排程、bytecode 程式、Huffman/LZ 壓縮表與各階段中繼資料，完全不依賴商業樣本檔案或外部擷取的 stub。

原生保護支援 x86 與 x64 的 EXE 及 DLL，涵蓋四種結構版面家族（`pe32`、`pe64-classic`、`pe64-modern` 與 `legacy-dll`）。Managed 保護則透過產生的 ECMA-335 啟動型別與獨立原生解碼器封裝 IL 組件。相容性皆經未修改的 Senbei 1.3.1 驗證，並於 Windows 11 組建 26100 實際執行原始檔、受保護檔與解包還原檔（目標平台為 Windows 10 與 Windows 11）。

內嵌執行階段實作了依 `%TEMP%` 資料夾啟用的除錯記錄、位於手動映射輔助 DLL 內的可設定環境檢查、透過 `KiUserExceptionDispatcher` 攔截存取違規並即時解密的頁面加密、依種子變異的載入器程式碼，以及啟動後的中繼資料抹除機制。檢查未通過時會將 `AAA-BBB-CCC` 結束代碼寫入啟用中的記錄檔；原生 EXE 預設會在終止前引發 `EXCEPTION_ACCESS_VIOLATION`（`--antidebug-av=on`）以讓附加的除錯器中斷，而 DLL、設定 `--antidebug-av=off` 的原生 EXE 與 Managed 模組則直接呼叫 `TerminateProcess`。

底層格式細節請參閱 [CrackProof for Windows 內部機制](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/)；靜態解包機制則記錄於 [Senbei](https://app.gitbook.com/s/v6LkixcUwwnaXW5PFCVE/)。

## 本區內容

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-terminal"></i></td><td><strong>使用說明</strong></td><td>CLI 的 <code>protect</code>、<code>inspect</code> 與 <code>verify</code> 命令、版面設定檔、環境檢查、頁面加密與除錯記錄。</td><td><a href="usage.md">使用說明</a></td></tr><tr><td><i class="fa-window-maximize"></i></td><td><strong>GUI 介面</strong></td><td>提供批次工作佇列、逐列設定檔與檢查項目覆寫、匯出 PowerShell 腳本與驗證功能的 WPF 前端。</td><td><a href="gui.md">GUI 介面</a></td></tr><tr><td><i class="fa-circle-check"></i></td><td><strong>支援範圍</strong></td><td>支援的原生與 Managed 家族、已測試的 CLR 宿主環境、封裝階段拒絕條件與結構上限。</td><td><a href="support.md">支援範圍</a></td></tr><tr><td><i class="fa-diagram-project"></i></td><td><strong>架構設計</strong></td><td>Crate 邊界、單份儲存的區段與資源編碼、三階段啟動流程，以及與商業版的剩餘差異。</td><td><a href="design.md">架構設計</a></td></tr><tr><td><i class="fa-hammer"></i></td><td><strong>開發指南</strong></td><td>建置原生載入器與 Managed 工具、執行 Senbei 1.3.1 對照驗證，以及 workspace 開發規範。</td><td><a href="development.md">開發指南</a></td></tr></tbody></table>

## 範圍與授權條款

Android 目標、獨立的 IL2CPP `global-metadata.dat` 混淆，以及 `protect` 中的核心驅動程式選項皆不在支援範圍內（實驗性核心驅動專案另置於 `kernel/` 目錄下）。

{% hint style="info" %}
**授權拆分。** 主機端工具（`arare-cli`、`arare-engine`、`tools/managed`、`gui` 與 `verification/senbei-oracle`）採用 `AGPL-3.0-only` 授權。PE 解析器（`arare-pe`）、編解碼器（`arare-codec`）及所有內嵌的原生與 Managed 執行階段程式碼（`arare-runtime`、`runtime/`）皆採用 `MIT` 授權，因此受保護的二進位檔不會嵌入任何 AGPL 程式碼。
{% endhint %}
