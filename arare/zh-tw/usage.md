---
description: "命令行保護、檢查與驗證：配置文件、檢查項、頁加密與發佈。"
---

# 用法

普通構建產出 `target/release/arare.exe`，不需要 Senbei 檢出。託管打包需要另行構建的託管工具與 .NET 10 運行時。把三個託管工具文件放入 `arare.exe` 旁的 `managed/` 目錄，或把 `ARARE_MANAGED_TOOLS` 設為這些文件所在的絕對目錄；詳見[開發](development.md)。生成相同命令行的 WPF 前端見[圖形界面](gui.md)。

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

受保護模塊在啟動期間運行可配置的環境檢查。大多數檢查在載荷重建前運行；可選的 E55/E91 設備檢查在頁密封后運行。檢查失敗時靜默結束進程。啟用日誌時，調試日誌會記錄檢查的階段碼。大多數階段碼遵循已觀察到的 CrackProof 行為；`541` 是 Arare 自己的 Hyper-V 來賓策略。

默認啟用的檢查如下：

| 模塊 | 檢查 |
| --- | --- |
| 原生 EXE | `antidebug`、`crc-loader`、`debug-port`、`os-version`、`boot-options`、`vm-registry`、`injected-dll`、`injected-thread`、`clean-code` |
| 原生 DLL | `crc-loader`、`vm-registry`、`host-process` |
| 託管 EXE | `crc-loader`、`vm-registry` |
| 託管 DLL | `crc-loader`、`vm-registry`、`host-process` |

其餘檢查默認關閉。因此兩類 DLL 默認都需要兼容的受保護 EXE。`vm-backdoor`、`parent-process` 與 `hyperv-guest` 對所有模塊類型都需要顯式啟用。

`--check NAME=on|off` 切換單項檢查。重複該標誌以組合覆蓋。

| 名稱 | 階段 |
| --- | --- |
| `antidebug` | 410 |
| `crc-loader` | 510 |
| `debug-port` | 520 |
| `kernel-debugger` | 52F |
| `vm-backdoor` | 540 |
| `hyperv-guest` | 541（Arare 專用） |
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

`vm-backdoor` 仍需顯式啟用。`--check vm-backdoor=on` 探測 VMware 後門協議，並在收到匹配響應時拒絕運行。它允許 Hyper-V/VBS 環境；通用的 CPUID 虛擬機監控程序標誌位不會觸發拒絕。顯式指定 `--check parent-process=on` 仍會拒絕除 `cmd.exe` 或 `explorer.exe` 以外的啟動器。

**強烈不建議啟用：** `hyperv-guest` 是獨立檢查，對所有模塊類型默認關閉。`--check hyperv-guest=on` 根據經校驗的 `Hv#1` CPUID 分區權限拒絕報告為 Hyper-V 兼容來賓的環境。它允許主機/根分區（包括 VBS），也允許無法判斷或信息不完整的環境。來賓檢測依賴啟發式判斷，嵌套環境、信息屏蔽或偽造都可能繞過分類。這是兼容性限制，不能提供可靠保護。

`vm-registry` 默認仍然啟用。當 `Hv#1` 接口表明環境兼容 Hyper-V 時，該檢查允許 `Virtual`、`VRTUAL` 與 `Microsoft Hyper-V` 這些通用註冊表標記。其他虛擬機廠商的明確標記仍會觸發拒絕。是否拒絕 Hyper-V 兼容來賓，由獨立且需顯式啟用的 `hyperv-guest` 決定。

已有受保護文件保留生成時使用的檢查實現。要應用修訂後的檢查與默認值，使用更新後的構建重新保護原始輸入。GUI 或命令腳本中保存的顯式 `on` 覆蓋仍然有效；對於不需要的可選限制，清除覆蓋或將其設為 `off`。

`host-process` 接受兼容的原生與託管 Arare EXE，包括不同打包種子。用 `--check host-process=off` 可在普通主機中加載受保護 DLL。`host-stamp` 只為已啟用 `host-process` 的 DLL 增加校驗。可選戳記是協作式運行時兼容性檢查，不是密碼學認證。

啟用 `disk-integrity` 會取代 `clean-code`，即使同時指定兩者。兩者都會把加載器調用路由到原始系統代碼副本；`disk-integrity` 還會對照可信系統映像校驗磁盤映像。

`os-version`（C00）使用 Arare 的下限：Windows 10 內部版本 10240。一份已觀察的商用樣本使用 14251。

`legacy-debugger`、`openark-device` 與 `cheat-engine-device` 為可選，默認關閉。僅憑佈局族名稱不能確定商用構建的選項默認值。

## 頁加密

`--page-encrypt=on` 時，加載器在重建後把可執行應用程序頁就地重新加密，並設為 `PAGE_NOACCESS`。stub 模塊的處理程序在首次觸及時解密該頁。頁密文在運行時創建；文件載荷仍使用所選格式的編碼。默認情況下主機 EXE 開啟、DLL 關閉，與已觀察到的配置一致。

`--scribble=on` 在故障之間對駐留已解密頁的選定字節做 XOR。它要求頁加密，默認關閉。

`--errlog=on` 嘗試向 `\\.\mailslot\ErrLog-Pec<suffix>` 發送診斷報告，其中 `<suffix>` 是根據日誌身份派生的四位十六進制數。報告包含時間戳、結束碼 `AAA-BBB-CCC` 與模塊路徑；失敗報告還可能包含已加載模塊或 OS 詳情。該通道獨立於調試日誌文件夾，默認關閉；只有匹配的郵件槽存在監聽方時才能送達。

含可寫可執行節的輸入需要 `--page-encrypt=off`。有效的默認開啟與顯式開啟會在發佈或替換任一輸出之前拒絕它們。

## 調試日誌

`protect --json` 返回 `log_folder`，即模塊自身的 12 位大寫十六進制日誌身份。在 `%TEMP%` 下創建該文件夾即可啟用其日誌。創建時間須在 48 小時內。運行時不會創建缺失的門控目錄。

DLL 跨打包種子繼承其受保護 EXE 的門控與文件夾。主機門控缺失、過期或無效時，即使 DLL 自己的門控是新的，也會抑制 DLL 日誌。沒有受保護主機上下文時，DLL 使用自己的門控。使用受保護主機時，應採用 EXE 報告的 `log_folder`；DLL 報告的值標識其後備文件夾。

主機校驗與日誌相互獨立：`host-process=off` 不會關閉繼承。EXE 使用 `HHMMSSmmmE-...` 文件名，DLL 使用 `HHMMSSmmmD-...`。

## 輸出

保護會在發佈前解析並編碼完整表示。輸出文件先暫存、刷新，再重命名。目標目錄必須已經存在。輸入的規範路徑或符號鏈接別名會被拒絕。替換不同硬鏈接上的輸出會替換該目錄項，並保留輸入字節。

固定種子會為相同輸入、選項與已編譯加載器復現輸出。更換編譯器、運行時源碼或元數據寫入器可能改變字節。
