---
description: "受保護 Windows PE、Android SO 與 IL2CPP 中繼資料的靜態解包與檢查工具。"
icon: screwdriver-wrench
---

# Senbei

Senbei（`1.4.0`）是針對受 CrackProof 保護之二進位檔所設計的靜態解包與結構檢查工具，可直接從單一檔案、Android 應用程式套件與目錄還原並驗證二進位檔，全程不會執行目標程式或附加至目標行程。

Windows 與 Linux 原生發行版同時包含 `senbei` 命令列工具與 `senbei-gui` 桌面工作台，內建英文、簡體中文、繁體中文、日文與韓文介面。同一套核心引擎亦提供 WebAssembly 版本，可在瀏覽器本機端直接處理獨立的 Windows PE 與中繼資料檔案。

## 支援的輸入格式

* **Windows PE（`PE32` 與 `PE32+`）：** 受保護的 `.exe` 與 `.dll` 模組（原生與 Managed .NET），包含外部 `.exe._` 與 `.dll._` 附屬酬載檔。
* **Android 原生程式庫（`ELF64` AArch64）：** 獨立的受保護 `.so` 檔案，以及 `.apk`、`.apks` 或 `.xapk` 應用程式套件。
* **Unity IL2CPP 中繼資料：** `global-metadata.dat` 檔案，涵蓋 Windows `-GMD`（`v31`）以及 Android 種子衍生（`v24.1`、`v29`、`v31`、`v39`）或內嵌 XOR（`v24`）版面配置。

底層容器格式與資料轉換細節請參閱 [CrackProof for Windows 內部機制](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/) 與 [CrackProof for Android SO 內部機制](https://app.gitbook.com/s/HezwIJwx0lhm5CUG7g8R/)。

## 本區內容

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-terminal"></i></td><td><strong>使用說明</strong></td><td>CLI 命令（<code>unpack</code>、<code>inspect</code>、<code>--dry-run</code>、<code>--json</code>）、資料夾與套件處理規則、顯示語言、旗標與結束代碼。</td><td><a href="usage.md">使用說明</a></td></tr><tr><td><i class="fa-window-maximize"></i></td><td><strong>GUI 介面</strong></td><td>原生桌面工作台（<code>senbei-gui</code>）：視覺化批次佇列、詳細分析檢視器、十六進位與 RVA 檢視、PE 比較與設定。</td><td><a href="gui.md">GUI 介面</a></td></tr><tr><td><i class="fa-diagram-project"></i></td><td><strong>架構設計</strong></td><td>九個 crate 的 workspace 架構、profile 與追蹤機制、Windows 與 Android 還原管線，以及 WebAssembly 邊界。</td><td><a href="design.md">架構設計</a></td></tr><tr><td><i class="fa-hammer"></i></td><td><strong>開發指南</strong></td><td>建置 CLI、桌面版 GUI 與 WebAssembly 目標，執行樣本集／模糊測試／一致性測試、效能基準測試與環境變數。</td><td><a href="development.md">開發指南</a></td></tr></tbody></table>

## 介面總覽

| 介面 | 支援目標 | 輸出與報告 |
| --- | --- | --- |
| `senbei`（CLI） | 單一檔案、資料夾、`.apk`/`.apks`/`.xapk` | 還原後的檔案、執行記錄檔、彩色終端機輸出、`--json` schema v1 報告 |
| `senbei-gui`（桌面版） | 單一檔案、資料夾、`.apk`/`.apks`/`.xapk` | 還原後的檔案、互動式 **概覽**／**詳細分析**／**十六進位**／**比較**／**條目**／**記錄** 分頁、匯出 JSON 與純文字報告 |
| 瀏覽器版（`web/`） | 單一 Windows PE 檔案（含 `._` 附屬檔）與 `global-metadata.dat` | 瀏覽器本機下載與 `Export JSON` 報告（輸入檔案不會離開本機裝置） |
