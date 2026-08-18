---
description: "受保護宿主、原生 DLL 和託管 DLL 的脫敏調試日誌。"
---

# 調試日誌示例

這些是真實的 CrackProof 調試日誌，捕獲方式是在 `%temp%` 下創建該可執行文件對應的 12 位十六進制字符文件夾並啟動受保護程序（見[調試日誌](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/runtime/startup-status)）。路徑與產品名已替換為通用佔位符；其餘一切——選項標誌、狀態碼、地址、hook 列表——均為原文。

## 如何閱讀日誌

* **第 1 行**——受保護模塊的路徑。
* **第 2 行**——該構建打包時使用的保護選項標誌（每個 `-XX` 記號對應一個打包器選項）。
* **第 3/4 行**——時間戳與模塊的加載基址。
* **後續行**——12 位[狀態碼](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/runtime/startup-status)，每個 stage 一行；縮進的 `000`–`00N` 行攜帶 stage 特定的細節（地址、計數、被 hook 的函數）。
* **最後幾行**——完成時間戳與 9 位錯誤碼（`000-000-000` = 成功）。

## 宿主 EXE——功能完整，頁加密

```
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

值得注意的點：

* `C03` 給出驅動代際：`Htsysm7679`——第二代 Htsysm（見 [Htsysm 內核組件](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/runtime/kernel-components)）。
* `C04` 列出為 Protected-Process 開關 hook 的全部 API（`NtCreateSection`、`NtAlpcSendWaitReceivePort`、`NtDuplicateObject`、`NtConnectPort`、`NtOpenProcess`、`NtOpenThread`……）以及加載器攔截 hook（`CreateProcessInternal*`、`CreateRemoteThread*`、`LdrLoadDll`、`CreateActCtxW`）。
* `640 … 840`——該模塊是**頁加密**的：先整體解密，隨後重新加密並安裝異常處理 hook。`840` 之後的 `002` 行攜帶三個地址（重新加密的區間與處理程序數據）。
* `570` 與 `A06` 在啟動後期 hook 更多 API（`user32!SetFocus`、`CreateWindowExA/W`、`uxtheme!ThemeInitApiHook`）。
* `660` 是一個不在公開狀態表中的 stage——在此處出現於 `840` 與最終的 `280`（跳轉 OEP）之間。

## 原生插件 DLL——僅整體解密

```
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

值得注意的點：

* `A11`——DLL 的宿主進程檢查，僅存在於受保護 DLL。
* **沒有 `640`/`840`**——該構建只整體解密一次（`610`），從不做頁加密；對比上面的宿主 EXE。頁加密是逐模塊的選項。
* `800` 攜帶單個地址——新填充的映像區域。

## 託管 DLL——最簡序列

```
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

託管構建運行最短的流水線：環境檢查、節解密（`610`），然後直達 OEP（`280`）——無驅動初始化、無頁加密、無重定位 stage。
