---
description: "受保护宿主、原生 DLL 和托管 DLL 的脱敏调试日志。"
---

# 调试日志示例

这些是真实的 CrackProof 调试日志，捕获方式是在 `%temp%` 下创建该可执行文件对应的 12 位十六进制字符文件夹并启动受保护程序（见[调试日志](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/yun-xing-shi/startup-status)）。路径与产品名已替换为通用占位符；其余一切——选项标志、状态码、地址、hook 列表——均为原文。

## 如何阅读日志

* **第 1 行**——受保护模块的路径。
* **第 2 行**——该构建打包时使用的保护选项标志（每个 `-XX` 记号对应一个打包器选项）。
* **第 3/4 行**——时间戳与模块的加载基址。
* **后续行**——12 位[状态码](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/yun-xing-shi/startup-status)，每个 stage 一行；缩进的 `000`–`00N` 行携带 stage 特定的细节（地址、计数、被 hook 的函数）。
* **最后几行**——完成时间戳与 9 位错误码（`000-000-000` = 成功）。

## 宿主 EXE——功能完整，页加密

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

值得注意的点：

* `C03` 给出驱动代际：`Htsysm7679`——第二代 Htsysm（见[内核驱动与子模块](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/yun-xing-shi/kernel-components)）。
* `C04` 列出为 Protected-Process 开关 hook 的全部 API（`NtCreateSection`、`NtAlpcSendWaitReceivePort`、`NtDuplicateObject`、`NtConnectPort`、`NtOpenProcess`、`NtOpenThread`……）以及加载器拦截 hook（`CreateProcessInternal*`、`CreateRemoteThread*`、`LdrLoadDll`、`CreateActCtxW`）。
* `640 … 840`——该模块是**页加密**的：先整体解密，随后重新加密并安装异常处理 hook。`840` 之后的 `002` 行携带三个地址（重新加密的区间与处理程序数据）。
* `570` 与 `A06` 在启动后期 hook 更多 API（`user32!SetFocus`、`CreateWindowExA/W`、`uxtheme!ThemeInitApiHook`）。
* `660` 是一个不在公开状态表中的 stage——在此处出现于 `840` 与最终的 `280`（跳转 OEP）之间。

## 原生插件 DLL——仅整体解密

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

值得注意的点：

* `A11`——DLL 的宿主进程检查，仅存在于受保护 DLL。
* **没有 `640`/`840`**——该构建只整体解密一次（`610`），从不做页加密；对比上面的宿主 EXE。页加密是逐模块的选项。
* `800` 携带单个地址——新填充的映像区域。

## 托管 DLL——最简序列

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

托管构建运行最短的流水线：环境检查、节解密（`610`），然后直达 OEP（`280`）——无驱动初始化、无页加密、无重定位 stage。
