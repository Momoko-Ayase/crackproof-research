---
description: "內嵌輔助 DLL（HtpecIt、HtdpStub2、cm、dm、sk、pm）與手動映射機制。"
icon: layer-group
---

# 手動映射輔助模組

CrackProof 不把主要的執行期子系統直接放在受保護二進位檔自身的區段內，而是將多個輔助 DLL 內嵌於載入器酬載中，在執行期由內部載入函式（`HtdpsCmnGetFileInfo`）依雙字母模組代號查找並載入。

## 子模組一覽

`HtdpsCmnGetFileInfo` 會將指定的輔助 DLL 手動映射至私有可執行記憶體（因此不會出現在 `InLoadOrderModuleList` 或 `CreateToolhelp32Snapshot` 走訪的 `PEB` 載入模組串列中），從其 PE 標頭解析進入點，並可在載入後抹除 `MZ` 與 `PE\0\0` 簽章：

| 雙字母代號 | 模組名稱 | 狀態碼範圍 | 執行期職責 |
| --- | --- | --- | --- |
| `it` | `HtpecIt.dll` | `Axx` | 使用者模式防竄改、反注入、VM 登錄檔與宿主行程檢查 |
| `dt` | `HtdpStub2.dll` | `8xx` / 分頁存取違規期間 | 隨選分頁解密例外處理常式（`KiUserExceptionDispatcher` 跳轉目標）與分頁描述表 |
| `cm` | （使用者模式輔助模組） | `Bxx` | 第 1 代 `Htsysm` 驅動程式部署與初始化 |
| `dm` | （使用者模式輔助模組） | `Cxx` | 第 2 代與第 3 代 `Htsysm` 驅動程式部署與 IOCTL 交握 |
| `sk` | `HtsyskNT.dll` | `B21` | 第 1 代核心模式 DLL：核心手動映射器與記憶體／I/O 存取原語 |
| `pm` | `HtpecmNT.dll` | `BB0` | 第 1 代核心模式 DLL：行程監控與強制終止 |

由於分頁解密常式以及區間／分頁描述元陣列全都位在 `dt`（`HtdpStub2.dll`）內（參見[分頁保護與載入器程式碼](page-protection.md)），若只傾印主程式 `.exe` 或 `.dll` 模組，就會完全漏掉分頁例外處理常式；分析時需掃描私有可執行的 VAD 記憶體區間，或直接順著 `ntdll!KiUserExceptionDispatcher` 開頭的 Inline Jump 追蹤，才能定位出 `dt`。核心端對應元件則整理於 [Htsysm 核心元件](kernel-components.md)。
