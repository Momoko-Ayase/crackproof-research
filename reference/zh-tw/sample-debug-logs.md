---
description: "擷取自頁面加密宿主 EXE、原生外掛 DLL 與 Managed DLL 的去識別化執行階段除錯記錄。"
icon: file-lines
---

# 除錯記錄範例

啟動程式前先於 `%temp%` 底下建立各二進位檔專屬的 12 位十六進位字元資料夾，即可擷取真實的 CrackProof 執行階段記錄（請參閱 [除錯記錄](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/runtime/startup-status#debug-logging)）。下列檔案路徑與產品名稱已替換為通用代稱；保護器選項旗標、狀態碼、記憶體位址與被 hook 的 API 清單皆保留原始輸出。

## 記錄檔結構

* **第 1 行：** 受保護 EXE 或 DLL 的完整檔案路徑。
* **第 2 行：** 編譯進該模組的保護器選項標記（如 `-CF`、`-CP`、`-PP` 等）。
* **第 3 與第 4 行：** 啟動時間戳記與十六進位模組載入基底位址。
* **主體行：** 12 位元[狀態碼](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/runtime/startup-status#the-boot-sequence-and-status-codes)，搭配縮排的 `000`..`00D` 明細行記錄各階段參數、驅動程式名稱與被 hook 的函式位址。
* **結尾行：** 結束時間戳記與 `AAA-BBB-CCC` 結果碼（正常啟動完成時為 `000-000-000`）。

## 實測擷取記錄

{% tabs %}
{% tab title="宿主 EXE（頁面加密）" %}
此筆追蹤記錄的觀察重點：

* **`C00`（`01A065F4 01A037AB`）：** 每個 dword 格式皆為 `0x01A00000 + build`，記錄主機端 Windows 組建編號 `26100`（`0x65F4`）以及最低允許組建編號 `14251`（`0x37AB`）。
* **`C03` 與 `C04`：** 初始化第 2 代驅動程式 `Htsysm7679`（請參閱 [Htsysm 核心元件](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/runtime/kernel-components)），並 hook 15 個 `kernel32` / `kernelbase` / `ntdll` API，以便在執行不相容的系統呼叫前後動態切換受保護行程（Protected Process）狀態。
* **`610 -> 640 -> 655 -> 6E1 -> 800..840 -> 660 -> 280`：** 批次解密可執行區段（`640`）、套用重定位（`655`）、hook `KiUserExceptionDispatcher` 並將頁面權限設為 `PAGE_NOACCESS`（`840`）、執行頁面保護後的交接程序 `660`，最後跳轉至 OEP（`280`）。

```text
E:\Package\app.exe
 -CF -CP -C2 -E2 -CC -T12 -RC3 -GWH -DA -DD -PP -I -EL5 -CK2 -CD1 -CD2 -CD3 -CD4 -EUT64 -DE -NCP2 -NC -NE -NCC2 -NRC -NDA3 -NEL -NEL2 -NEL3 -NEL4 -NELA -NEVS -NERR -NWEB -NEUT32 -NDEP1 -NDC -NPD
2026/05/15 04:55:07.178
 00007FF7`B2850000
200
 000 00001000 00000000 
410
510
520
540
560
A03
561
C00
 001 01A065F4 01A037AB
C01
C02
C03
 001 Htsysm7679
 005 E0ED7281 FFFFF806 386C0000 A6D4B2B6
C04
 004 05F8 00220000
 003 03 00007FF9`2F7BAA40 kernel32.dll!CreateProcessInternalA
 003 03 00007FF9`2DB4DCD0 kernelbase.dll!CreateProcessInternalA
 003 03 00007FF9`2F7BAAC0 kernel32.dll!CreateProcessInternalW
 003 03 00007FF9`2DB4E320 kernelbase.dll!CreateProcessInternalW
 003 03 00007FF9`2F7A2E20 kernel32.dll!CreateRemoteThread
 003 03 00007FF9`2DB6E050 kernelbase.dll!CreateRemoteThreadEx
 003 03 00007FF9`304BF7C0 ntdll.dll!LdrLoadDll
 003 03 00007FF9`305E2430 ntdll.dll!NtCreateSection
 003 03 00007FF9`305E2CA0 ntdll.dll!NtAlpcSendWaitReceivePort
 003 03 00007FF9`2F7A49A0 kernel32.dll!CreateActCtxW
 003 03 00007FF9`2DBA1160 kernelbase.dll!CreateActCtxW
 003 03 00007FF9`305E2270 ntdll.dll!NtDuplicateObject
 003 03 00007FF9`305E2F60 ntdll.dll!NtConnectPort
 003 03 00007FF9`305E1FB0 ntdll.dll!NtOpenProcess
 003 03 00007FF9`305E4200 ntdll.dll!NtOpenThread
A09
A0F
A08
A07
 002 01 00
5D0
552
570
 001 00007FF9`2F79F7D0 00007FF7`B2933A50 00007FF7`B2933560 00007FF7`B2933740
 00C 001F
 00D 0000 0000 0000 0000 0000 0000
590
5B0
598
5A0
A06
 003 23 00007FF9`2F9C3420 user32.dll!!SetFocus
 003 03 00007FF9`2DA71C20 win32u.dll!NtUserSetFocus
 003 03 00007FF9`26F25580 uxtheme.dll!!ThemeInitApiHook
 003 03 00007FF9`2F97D310 user32.dll!CreateWindowExA
 003 03 00007FF9`2F97D920 user32.dll!CreateWindowExW
5C0
5E1
610
640
655
6E1
800
 001 00007FF7`B294DC00
810
820
840
 002 00007FF7`B28F3010 00007FF7`B294B950 00007FF7`B294B820
 001 04F0
660
280
2026/05/15 04:55:07.278
000-000-000
```
{% endtab %}

{% tab title="原生外掛 DLL（一次性批次解密）" %}
此筆追蹤記錄的觀察重點：

* **`A11` -> `5D0` -> `A15`：** `A11` 驗證宿主 EXE 帶有 CrackProof 宿主標記；`A15` 則於 `5D0` 之後輸出，作為代表宿主驗證已通過的純 DLL 流程標記。
* **無 `640` / `840`（`-NCP`）：** 各區段於 `610` 一次解密完成，於 `655` 套用重定位，接著依序經過 `800 -> 830 -> 280`，所有程式碼頁面皆直接常駐於記憶體中。

```text
E:\Package\app_Data\Plugins\native_plugin.dll
 -CF -C2 -E2 -CC -T12 -RC3 -GWH -DA -DD -PP -I -EL5 -CK2 -CD1 -CD2 -CD3 -CD4 -DE -NCP -NCP2 -NC -NE -NCC2 -NRC -NDA3 -NEL -NEL2 -NEL3 -NEL4 -NELA -NEVS -NERR -NWEB -NEUT32 -NEUT64 -NDEP1 -NDC -NPD
2026/05/15 04:55:14.518
 00007FF8`31480000
200
 000 00001000 00000000 
510
540
560
A09
A11
5D0
A15
590
5B0
5A0
5C0
5E1
610
655
6E1
800
 001 00007FF8`317C4000
830
280
2026/05/15 04:55:14.619
000-000-000
```
{% endtab %}

{% tab title="Managed DLL" %}
此筆追蹤記錄的觀察重點：

* 執行精簡的 CLR DLL 啟動流程：`510` 載入器 CRC 檢查、`A09` 虛擬機器登錄檔檢查、`A11` 宿主 EXE 檢查、解密前置階段 `5D0..5A0`、於 `610` 解密區段與方法主體，隨即於 `280` 交接控制權（不執行驅動程式初始化、重定位或頁面加密保護）。

```text
E:\Package\app_Data\Managed\Assembly-CSharp.dll
 -CF -CP -C2 -E2 -CC -T12 -RC3 -GWH -DA -DD -PP -I -EL5 -CK2 -CD1 -CD2 -CD3 -CD4 -EUT64 -DE -NCP2 -NC -NE -NCC2 -NRC -NDA3 -NEL -NEL2 -NEL3 -NEL4 -NELA -NEVS -NERR -NWEB -NEUT32 -NDEP1 -NDC -NPD
2026/05/15 04:55:09.342
 00000174`0D290000
200
 000 00001000 00000000 
510
560
A09
A11
5D0
590
5B0
5A0
610
280
2026/05/15 04:55:09.368
000-000-000
```
{% endtab %}
{% endtabs %}
