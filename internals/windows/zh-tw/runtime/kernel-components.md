---
description: "三代 Htsysm 核心驅動架構：Ring-0 shellcode、EPROCESS 修改與控點權限過濾。"
icon: gears
---

# Htsysm 核心元件

CrackProof 選配的核心保護層（`Htsysm`）先後演進出三代截然不同的驅動程式架構：

{% tabs %}
{% tab title="第 1 代：HtsysmNT" %}
### 未經驗證的核心 shellcode 執行

第 1 代驅動對外開放了一組未經驗證的 IOCTL，可直接以 Ring-0 權限執行呼叫端傳入的 shellcode。CrackProof 的使用者模式輔助模組 `cm` 會利用這項原語，將兩個核心模式 DLL（狀態碼 `B21` 的 `HtsyskNT.dll` 與狀態碼 `BB0` 的 `HtpecmNT.dll`）手動映射進核心空間，並呼叫其匯出的 `_FarEntry@0` 以執行核心記憶體存取與行程終止。由於本機任何使用者模式行程都能送出同一組 IOCTL，一旦安裝此驅動，等於讓整台機器上的任意程式都取得 Ring-0 任意程式碼執行能力。
{% endtab %}

{% tab title="第 2 代：Htsysm7679" %}
### 限定範圍的 `EPROCESS` 遮罩 DWORD 修改（`0xAA01`）

第 2 代（`Htsysm7679`，裝置類型 `0xAA01`，IOCTL 為 `0xAA013880` / `0xAA013884` / `0xAA013888`）移除了通用的 shellcode 執行功能，改為針對 `IoGetCurrentProcess() + offset`（限制無號數 `offset < 0x1000`）執行帶遮罩的 32 位元清除、設定或讀取操作。

* **受保護行程（`PP`）切換：** 在階段 `C03` / `C04`，載入器會設定目前行程 `EPROCESS` 內的受保護行程（Protected Process）位元欄位，阻止使用者模式的除錯器與注入工具開啟完整權限控點。由於啟用 `PP` 會導致部分 Win32 / NT 呼叫（如 `NtCreateSection`）失敗，使用者模式載入器會在 `C04` 對這些函式掛上 hook，先暫時清除 `PP`、呼叫原始 API，完成後再重新設回 `PP`。
* **BYOVD 攻擊面：** 驅動對呼叫端的驗證僅依賴一套可逆的 PID 加密轉換；本機任何行程只要重現該 PID 轉換，就能修改自身 `EPROCESS`（`offset < 0x1000`）內的欄位，或趕在目標行程於 `C04` 啟用 `PP` 之前先行注入。
{% endtab %}

{% tab title="第 3 代：Htsysm767901 與 Htsysm1B4001" %}
### `ObRegisterCallbacks` 控點權限過濾（`0xAA02`）

第 3 代（`Htsysm767901` 與 `Htsysm1B4001`，裝置類型 `0xAA02`，共 12 組 IOCTL `0xAA023800..0xAA02382C`）不再直接修改 `EPROCESS`，改以 `ObRegisterCallbacks` 向物件管理員註冊回呼（`Htsysm1B4001` 的回呼 Altitude 為衍生自 `1B4001` 的 `88180.011104000001`），最多追蹤 100 個受保護行程，並維護一組 12 筆項目的環狀記錄緩衝區。

* **剝除存取權限遮罩（`& 0xFFFFFFC5`，清除 `0x3A`）：** 針對未獲授權的控點開啟與複製（Duplicate）請求，一併拔除 `PROCESS_CREATE_THREAD`（`0x02`）、`PROCESS_VM_OPERATION`（`0x08`）、`PROCESS_VM_READ`（`0x10`）與 `PROCESS_VM_WRITE`（`0x20`）權限。
* **豁免規則：** 放行 `KernelHandle`、行程自我存取、最多 5 組預先設定的呼叫端 PID（`0xAA02380C`）、最多 3 組預先設定的呼叫端父行程 PID（`0xAA023810`），以及 `csrss.exe`、`lsass.exe`、`conhost.exe` 或 `svchost.exe`（**但前提是必須從設定的系統目錄下執行**，對應 `0xAA023800`；其中 `svchost.exe` 還必須符合 `0xAA023814` 設定的預期父行程 PID）。
* **三態交握驗證：** 註冊受保護行程時改採自身程式碼與返回位址雜湊驗證，不再使用靜態 PID 加密，且完全不向使用者模式呼叫端提供任何核心記憶體寫入原語。
{% endtab %}
{% endtabs %}

## 版本戳記（`0x7679` 與 `1B40`）

`Htsysm7679` / `Htsysm767901` 名稱中的 `0x00007679`，正對應 PE32 `EighthStage` 與第 5 階段特徵標記表中的 `0x00007679` 組態叢集戳記（參見 [PE32、DLL 與無特徵標記配置](../loading-and-pe-repair/loading/layout-variants.md)）。較新的 Windows 組建在 `C02` / `C03` 記錄 `Htsysm1B4001` 時，則與 Android 組建共用 `1B40` 世代戳記，採用第 3 代 `0xAA02` 回呼驅動（因此在 `C04` 需要 hook 的使用者模式 API 更少），且經常一併啟用 `E` 系列裝置檢查（`E55`、`E91`）。

## 元件總表

| 元件 | 所屬層級 | 職責 |
| --- | --- | --- |
| `HtpecIt.dll`（`it`） | 手動映射使用者模式 DLL | `Axx` 防竄改、反注入、VM 與宿主行程檢查 |
| `HtdpStub2.dll`（`dt`） | 手動映射使用者模式 DLL | 隨選分頁解密例外處理常式與分頁描述表 |
| `HtsyskNT.dll`（`sk`）/ `HtpecmNT.dll`（`pm`） | 第 1 代核心模式 DLL | 核心手動映射器（`B21`）與行程監控（`BB0`） |
| `HtsysmNT` | 核心驅動程式（第 1 代） | 未經驗證的 Ring-0 shellcode 執行 |
| `Htsysm7679` | 核心驅動程式（第 2 代，`0xAA01`） | 目前行程 `EPROCESS` 的限定範圍（`offset < 0x1000`）遮罩 DWORD 修改 |
| `Htsysm767901` / `Htsysm1B4001` | 核心驅動程式（第 3 代，`0xAA02`） | `ObRegisterCallbacks` 控點權限過濾與路徑／PID 豁免機制 |
