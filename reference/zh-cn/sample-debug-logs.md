---
description: "采自页面加密宿主 EXE、原生插件 DLL 与托管 DLL 的脱敏运行时调试日志。"
icon: file-lines
---

# 调试日志示例

以下为真实的 CrackProof 运行时日志，启动前在 `%temp%` 下创建各二进制文件对应的 12 字符十六进制目录即可采集（详见 [调试日志](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/runtime/startup-status#debug-logging)）。文件路径与产品名称已替换为通用占位符；加壳选项标记、状态码、内存地址与被 hook 的 API 列表均原样保留。

## 日志结构

* **第 1 行：** 受保护 EXE 或 DLL 的完整路径。
* **第 2 行：** 编译进该模块的加壳选项标记（如 `-CF`、`-CP`、`-PP` 等）。
* **第 3 至 4 行：** 启动时间戳与十六进制模块加载基址。
* **主体行：** 12-bit（3 位十六进制）[状态码](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/runtime/startup-status#the-boot-sequence-and-status-codes)，缩进的 `000`..`00D` 明细行则记录阶段参数、驱动名称及被 hook 的函数地址。
* **结尾行：** 结束时间戳与 `AAA-BBB-CCC` 结果码（正常启动完成时为 `000-000-000`）。

## 采集日志原文

{% tabs %}
{% tab title="宿主 EXE（页面加密）" %}
本段日志的关键信息：

* **`C00`（`01A065F4 01A037AB`）：** 每个双字均为 `0x01A00000 + build`，分别记录当前宿主机 Windows build 号 `26100`（`0x65F4`）与最低允许 build 号 `14251`（`0x37AB`）。
* **`C03` 与 `C04`：** 初始化第二代驱动 `Htsysm7679`（见 [Htsysm 内核组件](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/runtime/kernel-components)），并 hook 15 个 `kernel32` / `kernelbase` / `ntdll` API，在不兼容的系统调用前后临时切换受保护进程（Protected Process）状态。
* **`610 -> 640 -> 655 -> 6E1 -> 800..840 -> 660 -> 280`：** 整块解密可执行节（`640`），应用重定位（`655`），hook `KiUserExceptionDispatcher` 并将代码页设为 `PAGE_NOACCESS`（`840`），执行收尾交接步骤 `660`，最后跳转至 OEP（`280`）。

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

{% tab title="原生插件 DLL（整块解密）" %}
本段日志的关键信息：

* **`A11` -> `5D0` -> `A15`：** `A11` 校验宿主 EXE 是否带有 CrackProof 宿主特征标记；`A15` 在 `5D0` 之后输出，作为确认宿主校验已通过的纯 DLL 流程标记。
* **无 `640` / `840`（`-NCP`）：** 各节在 `610` 一次性完成解密，在 `655` 应用重定位，随后经 `800 -> 830 -> 280` 结束引导，所有代码页保持明文常驻内存。

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

{% tab title="托管 DLL" %}
本段日志的关键信息：

* 执行最精简的 CLR DLL 启动序列：`510` 加载器 CRC 校验、`A09` 虚拟机注册表检查、`A11` 宿主 EXE 检查、解密前序步骤 `5D0..5A0`、`610` 解密节与方法体，随后直接在 `280` 移交控制权（无驱动初始化、重定位或页面加密）。

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
