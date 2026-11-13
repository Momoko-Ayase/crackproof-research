---
description: "CLI 命令、結構檢查報告、資料夾與 Android 套件處理、顯示語言、旗標與結束代碼。"
icon: terminal
---

# 使用說明

```text
senbei [inspect|unpack] <file|folder> [--out DIR] [-v|--verbose] [-q|--quiet]...
    [--json] [--dry-run] [--threads N] [--color auto|always|never] [--scan-all]
    [--strict-integrity] [--max-entry-mib N] [--max-total-mib N]
    [--max-entries N] [--max-depth N] [--no-log] [--no-pause]
    [-V|--version] [-h|--help]
```

`senbei <path>` 等同於 `senbei unpack <path>`。當 `inspect` 與 `unpack` 置於 `<file|folder>` 之前時會解析為子命令（若要指定名為 `inspect` 的檔案或資料夾，請傳入 `./inspect` 或 `.\inspect`）。

## 常見工作流程

{% tabs %}
{% tab title="解包" %}
預設會在 `<上層目錄>/unpack/`（單一檔案）或 `<根目錄>/unpack/`（資料夾）下寫入還原後的檔案，並在副檔名前插入 `.unpack`；亦可透過 `--out DIR` 統一指定輸出檔案與執行記錄檔目錄：

```cmd
senbei app.exe
senbei app.exe --out C:\out
senbei game.apk --out C:\out
senbei "C:\Games\SampleTitle"
```

處理 `global-metadata.dat` 時，Senbei 僅在方法 token 或索引確實發生變更時才會寫出 `global-metadata.unpack.dat`；已是標準格式或不支援的版本在資料夾掃描中會自動略過，直接對單一檔案執行解包時則會回報錯誤。
{% endtab %}

{% tab title="結構檢查與 JSON" %}
`inspect` 會在記憶體中執行完整靜態還原以收集分析證據，不會寫入輸出檔案或執行記錄檔，也不會執行目標檔案：

```cmd
senbei inspect module.dll
senbei inspect module.dll --json
senbei inspect module.dll --strict-integrity --json
```

報告內容包含原始檔雜湊值、解析後的 PE/ELF/中繼資料標頭、解碼後的保護表、每條嘗試過的還原路徑與排除原因、最終採用的路徑、定位出的各階段參數（明確區分實體檔案偏移、附屬檔拼接偏移與工作映像 RVA），以及靜態驗證結果。
{% endtab %}

{% tab title="試執行與 CI" %}
`--dry-run` 會執行還原與靜態驗證，但不儲存輸出檔案或記錄檔（也不收集 `inspect` 追蹤細節）。Android 暫存解壓縮工作區會在結束時自動清理：

```cmd
senbei unpack module.dll --dry-run
senbei unpack module.dll --dry-run --json --strict-integrity
senbei unpack folder --strict-integrity --no-pause -q
```

`inspect` 與 `--dry-run` 皆不可與 `--out` 同時使用。
{% endtab %}
{% endtabs %}

## Android 程式庫與應用程式套件

Senbei 可還原受保護的 AArch64 `.so` 二進位檔（輸出為 `libil2cpp.unpack.so` 或 `<stem>.unpack.so`），並直接處理 `.apk`、`.apks` 與 `.xapk` 套件：

1. 先讀取 ZIP 中央目錄，並依 `--max-depth` 上限追蹤 `.apks`/`.xapk` 內的巢狀 `.apk` 條目。
2. 在設定的 `--max-entry-mib`、`--max-total-mib` 與 `--max-entries` 配額內，僅將 `.so` 與檔名完全相符的 `global-metadata.dat` 條目串流寫入暫存檔。
3. 將外部 `v24.1` 中繼資料與所屬應用程式的模組 `0x0C` 配對（跨 split APK 時依 `AndroidManifest.xml` 的套件名稱與版本配對，目錄模式下則依 `<root>/lib/<abi>/` 與 `<root>/assets/` 配對），將精簡型 `v24` XOR 資料解碼為 `global-metadata.unpack.dat`，並在獨立檔案與套件內檔案內容相同時去除重複項目。

## 資料夾掃描與附屬檔

資料夾模式會遞迴走訪子目錄，自動略過名為 `unpack` 的目錄（不分大小寫，除非根目標本身就叫 `unpack`），並略過根目錄以下的 NTFS 重新解析點（reparse point）子目錄：

* **掃描目標檔名（不分大小寫）：** `.exe`、`.dll`、`.so`、`global-metadata.dat`、`.apk`、`.apks` 與 `.xapk`。共用相同 manifest 套件名稱與版本的同層 split `.apk` 檔案會自動歸為同一組。除非設定 `--scan-all`（或環境變數 `SENBEI_SCAN_ALL`），否則小於 `4,128` 位元組的候選檔案預設不會開啟，直接略過。
* **Windows `._` 附屬檔：** 同目錄下的 `.exe._` 與 `.dll._` 檔案會由對應的 stub 合併讀取，不會計入已略過檔案。Managed 附屬 DLL 必須同時具備 `Module.dll` 與 `Module.dll._`，Senbei 才能將 stub 內的 `COR20` 資料表覆寫至解密後的 IL 方法主體上。

{% hint style="info" %}
**附屬檔診斷訊息。** 唯有當 PE32+ 入口記錄明確帶有 `._` 附屬檔宣告（`~0x1000` 與 `~"._\0\0"`）且缺少 `<input>._` 時，才會回報 `Missing companion file`。`Companion doesn't match` 代表 `<input>._` 短於 32 位元組，或其 `0x00..0x20` 標頭與 `stub[0x1000..0x1020]` 不一致。
{% endhint %}

## 顯示語言與終端機色彩

Senbei 支援五種顯示語言：`en`（英文）、`zh-CN`（簡體中文）、`zh-TW`（繁體中文）、`ja`（日文）與 `ko`（韓文）。

{% tabs %}
{% tab title="Command Prompt" %}
```cmd
set SENBEI_LANG=ja
senbei inspect module.dll
```
{% endtab %}

{% tab title="PowerShell" %}
```powershell
$env:SENBEI_LANG = "zh-TW"
senbei inspect module.dll
```
{% endtab %}

{% tab title="POSIX / Bash" %}
```sh
SENBEI_LANG=ko senbei inspect module.dll
```
{% endtab %}
{% endtabs %}

* **語系解析規則：** `SENBEI_LANG` 會先去除 `.encoding` 與 `@modifier` 後綴，不分大小寫比對 `-` 或 `_`，且文字系統子標籤（`Hans` / `Hant`）優先於地區碼（`zh-Hans-HK` -> 簡體中文；`zh-Hant`、`zh-TW`、`zh-HK`、`zh-MO` -> 繁體中文）。未設定 `SENBEI_LANG` 時，Senbei 會依序檢查 Windows UI 語言清單或 `LC_ALL` / `LC_MESSAGES` / `LANG` / `LANGUAGE`，皆無對應時回退為英文。
* **維持英文輸出的項目：** `--json` 輸出、儲存的 `.log` 記錄檔、`inspect` 結構證據表格，以及 `-v` 各階段明細行一律維持英文；若在地化錯誤訊息僅為詳細內部錯誤的摘要，下一行會接著印出完整的英文錯誤訊息。
* **色彩控制（`--color MODE` 或 `--color=MODE`）：** `auto`（預設）會依個別輸出串流檢查 TTY 狀態，並在 `NO_COLOR` 非空或 `TERM=dumb` 時停用色彩；`always` 會在一般文字輸出中強制啟用 ANSI 色彩；`never` 停用色彩。`--json` 輸出與 `.log` 檔案不會包含 ANSI 跳脫序列。

## 靜態驗證與瀏覽器限制

靜態驗證會檢查還原後的 PE 標頭、區段映射、進入點可達性與 CRT 分支目標、最多 256 筆匯入描述元、原生資料目錄與 CLR `BSJB` 資料流，同時檢查 Android ELF 的 `PT_LOAD` 範圍、動態表、符號雜湊表、重定位項目與建構函式指標。帶有結構警告或非致命錯誤的輸出在 `unpack` 時仍會寫入磁碟並標記為 `suspect`；加上 `--strict-integrity` 後，任何 `suspect` 結果（無論在 `unpack`、`--dry-run` 或 `inspect` 下）都會使結束代碼變為 `1`。

在 WebAssembly 瀏覽器應用程式中，**Input limit per module (MiB)** 預設為 `256`（範圍 `8`..`4096` MiB，會在讀入記憶體前合併計算 stub 與其 `._` 附屬檔大小），點選 **Export JSON** 可下載本機 `senbei.browser-report` v1 檔案。Android `.so` 與套件還原則須使用原生版 `senbei` 或 `senbei-gui`。

## 旗標一覽

| 旗標 | 行為說明 |
| --- | --- |
| `--out DIR` | 將解包後的檔案與執行記錄檔寫入 `DIR` 底下（僅限 `unpack` 模式）。 |
| `--dry-run` | 執行還原與驗證，但不儲存輸出檔案或記錄檔。 |
| `--json` | 在 `stdout` 輸出具版本號的 JSON 報告（即使搭配 `-q -q` 亦會輸出）；同時停用執行記錄檔與結束暫停提示。 |
| `--threads N` | 工作執行緒數量上限（`N >= 1`），會覆寫 `SENBEI_THREADS`（設為 `1` 時循序執行）。 |
| `--color auto\|always\|never` | 控制終端機 ANSI 色彩（亦接受 `--color=MODE`）。 |
| `-v`, `--verbose` | 印出各階段執行進度明細。 |
| `-q`, `--quiet` | 隱藏標題列與逐檔進度；分開傳入 `-q -q` 可關閉所有 `stdout` 與執行期 `stderr` 輸出。 |
| `--no-log` | 略過寫入 `senbei-YYYYMMDD-HHMMSS.log` 記錄檔。 |
| `--scan-all` | 在資料夾掃描時一併探測小於 `4,128` 位元組的目標檔名檔案。 |
| `--strict-integrity` | 若有任何還原映像標記為 `suspect`，即以結束代碼 `1` 結束（適用於 `unpack`、`--dry-run` 與 `inspect`）。 |
| `--max-entry-mib N` | 單一 Android ZIP 條目、解碼後容器、產物或輸出檔案的大小上限，單位為 MiB（`N >= 1`，預設 `2048`）。 |
| `--max-total-mib N` | Android 套件解壓縮與單一工作還原累計處理量的 MiB 配額上限，並非行程峰值記憶體上限（`N >= 1`，預設 `8192`）。 |
| `--max-entries N` | 跨巢狀 Android 套件的壓縮檔條目與 Stage 2 記錄數量上限（`N >= 1`，預設 `100000`）。 |
| `--max-depth N` | 巢狀 Android APK 與 Stage 2 串流的最大巢狀深度（允許 `0`，預設 `32`）。 |
| `--no-pause` | 從 Windows 檔案總管啟動時，略過結束前的互動暫停提示。 |
| `-V`, `--version` / `-h`, `--help` | 印出版本資訊或使用說明，並以結束代碼 `0` 結束。 |

## 結束代碼

| 代碼 | 意義 |
| --- | --- |
| `0` | 命令執行成功（`unpack`、`--dry-run`、`inspect`、`--help` 或 `--version`），無任何目標發生錯誤（啟用 `--strict-integrity` 時亦無 `suspect` 輸出）。 |
| `1` | 至少一個目標失敗、掃描或檔案探測無法讀取、超出 Android 資源配額限制，或在 `--strict-integrity` 下遇到 `suspect` 映像。 |
| `2` | 命令列引數無效（包含未帶任何引數呼叫 `senbei`、旗標彼此衝突，或數值限制無效）。 |
