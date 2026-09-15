---
description: 已觀察到的 Htsysm 代際、內核職責與版本標記。
---

# Htsysm 內核組件

## Htsysm 第一代：無鑑權的內核 shellcode（HtsysmNT）

最舊驅動的招牌特性是一個**讓任意進程執行內核態 shellcode 的無鑑權 IOCTL**。CrackProof 用它手動映射內核態 DLL（`HtsyskNT.dll`，然後是 `HtpecmNT.dll`），並調用它們的 `_FarEntry@0` 導出——其實現其餘內核功能，包括按模塊說明的監視並終止分析進程。

安全設計名副其實地糟糕：系統上的任何進程都能要求該驅動在 ring 0 運行任意代碼。

## Htsysm 第二代：EPROCESS 編輯（Htsysm7679）

第二代在意圖上受限得多：它讓進程**寫自己的 `EPROCESS`**，允許它編輯關於自身的信息。CrackProof 只使用其中一個特性：設置 **Protected Process（PP）標誌**，使用戶態工具無法打開、讀取或注入受保護進程（狀態 `C03`/`C04`）。

另外兩個細節：

* 某些 API 在 PP 下行為異常（`NtCreateSection` 在列），因此加載器鉤住這些函數：臨時摘掉 PP 標誌、調用原函數、再重新啟用。被鉤函數列表出現在調試日誌中。
* 訪問“鑑權”是一種按進程 ID 的加密方案——但任何能正確加密自身進程 ID 的程序都獲得同樣的 `EPROCESS` 寫原語，等價於任意內核內存訪問。第二條濫用路徑：在進程獲得 PP 之前注入 DLL，然後讓注入代碼享受受保護狀態。儘管如此，該驅動仍帶著有效的 WHQL 簽名發佈，成為實用的自帶漏洞驅動（BYOVD）候選。

解除 PP 標誌需要內核級手段（內核或虛擬機監控器調試器、PP 切換驅動，或在標誌設置前鉤住 `DeviceIoControl`）。

## Htsysm 第三代：句柄限制（Htsysm767901）

最新一代完全放棄了授予權限的做法。它改為**拒絕未批准進程以危險訪問權打開受保護進程的句柄**：`PROCESS_CREATE_THREAD`、`PROCESS_VM_OPERATION`、`PROCESS_VM_READ` 與 `PROCESS_VM_WRITE`。獲批進程是固定的系統二進制白名單（`svchost.exe`、`csrss.exe`、`lsass.exe`、`conhost.exe`）。

這一代的鑑權檢查比前代更徹底，不授予受保護進程任何特殊權力，對惡意軟件也沒有利用價值——是這條驅動線上第一個把自己限定在防禦上的設計。

## `0x7679` 版本戳

驅動名中編碼了構建戳：`Htsysm7679` 與 `Htsysm767901`（即 `7679` 變體 `01`）。同一 dword `0x00007679` 也出現在受保護文件內部，作為 32 位加載器最終階段的**配置簇戳**（見 [PE32、DLL 與無標記佈局](../loading-and-pe-repair/loading/layout-variants.md)），以及 stage-5 標記表內一個 8 字節標籤的一半。它充當把受保護構建與其驅動世代聯繫起來的版本標識符，在分類未知樣本時是有用的指紋。

## `Htsysm1B4001` 設備名

部分較新構建在 `C02`/`C03` 記下的設備名是 `Htsysm1B4001`，而不是 `Htsysm7679` 或 `Htsysm767901`。`1B40` 戳也出現在 Android 原生庫家族中。這是另一個已觀察的服務與設備名，不是擁有獨立權限模型的第四代。一份已觀察的該設備名日誌在 `C04` 列出的鉤子更少，並進入[啟動序列與狀態報告](startup-status.md)中的 `E` 段。

## 速查

| 組件              | 種類             | 用途                                |
| --------------- | -------------- | --------------------------------- |
| `HtpecIt.dll`   | 手動映射用戶態 DLL    | 防篡改/注入/VM 檢查（`Axx` 階段）            |
| `HtdpStub2.dll` | 手動映射用戶態 DLL    | 加載器擴展；頁錯誤按需解密處理器                  |
| `HtsyskNT.dll`  | 內核 DLL（經第一代驅動） | 內核手動映射器與 I/O（`B21`）               |
| `HtpecmNT.dll`  | 內核 DLL（經第一代驅動） | 進程監控/終止（`BB0`）                    |
| HtsysmNT        | 內核驅動，第一代       | 無鑑權內核 shellcode IOCTL             |
| Htsysm7679      | 內核驅動，第二代       | `EPROCESS` 寫；Protected Process 標誌 |
| Htsysm767901    | 內核驅動，第三代       | 句柄訪問權限制                           |
| Htsysm1B4001    | 設備/服務名          | 出現在 `1B40` 家族的 Windows 構建中           |
