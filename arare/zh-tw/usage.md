---
description: "命令行保護、檢查與驗證：配置文件、檢查項、頁加密與發佈。"
---

# 用法

普通構建產出 `target/release/arare.exe`，不需要 Senbei 檢出。託管打包需要另行構建的託管工具。生成相同命令行的 WPF 前端見 [圖形界面](gui.md)。

```text
arare protect INPUT --output OUTPUT --profile PROFILE
    [--seed 64_HEX_DIGITS] [--no-compression]
    [--storage embedded|companion] [--check NAME=on|off]...
    [--page-encrypt on|off] [--scribble on|off] [--errlog on|off]
    [--force] [--json]

arare inspect INPUT [--json]

arare verify INPUT --profile PROFILE [--companion PATH] [--json]
```

| 配置 | 輸入族 |
| --- | --- |
| `pe32` | PE32 x86/原生，以及適用的 x86/AnyCPU 託管映像 |
| `pe64-classic` | 經典 EXE 式 PE32+ x64 EXE 與 DLL |
| `pe64-modern` | 無標記 EXE 式 PE32+ x64 EXE 與 DLL |
| `legacy-dll` | 專用的較舊 PE32+ x64 DLL 族 |

選定的族會對照輸入驗證。它不對應公開的商用版本號。各族內的限制見 [支持範圍](support.md)。

伴生存儲產出命名的 PE 及其匹配的 `<filename>._` 文件。兩者須放在一起。覆蓋已有輸出需要 `--force`。省略種子時使用 Windows 密碼學隨機源，並在成功時打印。`--no-compression` 以原始形式存儲應用程序塊；必要的格式與生成的加載器階段仍使用各自的表示。

`verify` 用獨立的原生解碼器檢查表示。它不啟動程序。伴生驗證會在 32 字節配對頭匹配時自動嘗試 `<INPUT>._`。該自動文件缺失時會給出提示。

## 環境檢查

受保護模塊在解密前運行 CrackProof 風格的環境檢查。每一項記錄其觀察到的階段碼，失敗時靜默結束進程。

原生 EXE 使用較完整的已觀察檢查集。原生 DLL 啟用 `crc-loader`、`vm-backdoor`、`vm-registry` 與 `host-process`。託管模塊啟用 `crc-loader` 與 `vm-registry`；託管 DLL 另外啟用 `host-process`。因此兩類 DLL 默認都需要兼容的受保護 EXE。

`--check NAME=on|off` 切換單項檢查。重複該標誌以組合覆蓋。

| 名稱 | 階段 |
| --- | --- |
| `antidebug` | 410 |
| `crc-loader` | 510 |
| `debug-port` | 520 |
| `kernel-debugger` | 52F |
| `vm-backdoor` | 540 |
| `parent-process` | A03 |
| `os-version` | C00 |
| `boot-options` | C01 |
| `msc-log` | BD0 |
| `os-compat` | B00 |
| `vm-registry` | A09 |
| `injected-dll` | A0F |
| `injected-thread` | A07/A01 |
| `host-process` | A11 |
| `host-stamp` | 可選的 A11 運行時上下文校驗 |
| `clean-code` | A08 |
| `disk-integrity` | A04 |
| `legacy-debugger` | BE0 |
| `openark-device` | E55 |
| `cheat-engine-device` | E91 |

默認值按設計會產生誤報。`parent-process` 拒絕除 `cmd.exe`/`explorer.exe` 以外的啟動器。`vm-backdoor` 拒絕存在虛擬機監控程序的機器，包括 VBS/Hyper-V 主機。這類環境應關閉它們。

`host-process` 接受兼容的原生與託管 Arare EXE，包括不同打包種子。用 `--check host-process=off` 可在普通主機中加載受保護 DLL。可選戳記是協作式運行時兼容性檢查，不是密碼學認證。

`os-version`（C00）使用 Arare 的下限：Windows 10 內部版本 10240。一份已觀察的商用樣本使用 14251。

`legacy-debugger`、`openark-device` 與 `cheat-engine-device` 為可選，默認關閉。僅憑佈局族名稱不能確定商用構建的選項默認值。

## 頁加密

`--page-encrypt=on` 時，加載器在重建後把每個可執行應用程序頁就地重新加密，並設為 `PAGE_NOACCESS`。stub 模塊的處理程序在首次觸及時解密該頁。文件只攜帶描述符表，不攜帶密文。默認與已觀察構建一致：主機 EXE 開啟，DLL 關閉。

`--scribble=on` 在故障之間對駐留已解密頁的選定字節做 XOR。它要求頁加密，默認關閉。

`--errlog=on` 在日誌關閉時把結束碼 `AAA-BBB-CCC` 報告到 `\\.\mailslot\ErrLog-Pec`。默認關閉。

含可寫可執行節的輸入需要 `--page-encrypt=off`。有效的默認開啟與顯式開啟會在發佈或替換任一輸出之前拒絕它們。

## 調試日誌

在 `%TEMP%` 下創建該構建的 12 位十六進制文件夾以啟用日誌。其創建時間須在 48 小時內。運行時不會創建缺失的門控目錄。

DLL 跨打包種子繼承其受保護 EXE 的門控與文件夾。主機門控缺失、過期或無效時，即使 DLL 自己的門控是新的，也會抑制 DLL 日誌。沒有受保護主機上下文時，DLL 使用自己的門控。

主機校驗與日誌相互獨立：`host-process=off` 不會關閉繼承。EXE 使用 `HHMMSSmmmE-...` 文件名，DLL 使用 `HHMMSSmmmD-...`。

## 輸出

保護會在發佈前解析並編碼完整表示。輸出文件先暫存、刷新，再重命名。目標目錄必須已經存在。輸入的規範路徑或符號鏈接別名會被拒絕。替換不同硬鏈接上的輸出會替換該目錄項，並保留輸入字節。

固定種子會為相同輸入、選項與已編譯加載器復現輸出。更換編譯器、運行時源碼或元數據寫入器可能改變字節。
