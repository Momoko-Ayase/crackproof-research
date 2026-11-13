---
description: "Anonymized runtime debug logs captured from a page-encrypted host EXE, a native plugin DLL, and a managed DLL."
icon: file-lines
---

# Sample debug logs

Real CrackProof runtime logs captured by creating each binary's 12-hex-character folder under `%temp%` before launch (see [Debug logging](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/runtime/startup-status#debug-logging)). File paths and product names are replaced with generic placeholders; option flags, status codes, addresses, and hooked-API lists are verbatim.

## Log structure

* **Line 1:** full path of the protected EXE or DLL.
* **Line 2:** packer option tokens (`-CF`, `-CP`, `-PP`, etc.) compiled into that module.
* **Lines 3 and 4:** start timestamp and hexadecimal module load base.
* **Body lines:** 12-bit [status codes](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/runtime/startup-status#the-boot-sequence-and-status-codes), with indented `000`..`00D` detail lines carrying stage parameters, driver names, and hooked function addresses.
* **Closing lines:** end timestamp and `AAA-BBB-CCC` result (`000-000-000` on clean startup).

## Captured transcripts

{% tabs %}
{% tab title="Host EXE (page-encrypted)" %}
Key observations in this trace:

* **`C00` (`01A065F4 01A037AB`):** each dword is `0x01A00000 + build`, recording host Windows build `26100` (`0x65F4`) against minimum accepted build `14251` (`0x37AB`).
* **`C03` & `C04`:** initializes Generation-2 driver `Htsysm7679` (see [Htsysm kernel components](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/runtime/kernel-components)) and hooks 15 `kernel32` / `kernelbase` / `ntdll` APIs to toggle Protected Process state around incompatible system calls.
* **`610 -> 640 -> 655 -> 6E1 -> 800..840 -> 660 -> 280`:** bulk-decrypts executable sections (`640`), applies relocations (`655`), hooks `KiUserExceptionDispatcher` and seals pages `PAGE_NOACCESS` (`840`), runs post-seal handoff `660`, and jumps to OEP (`280`).

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

{% tab title="Native plugin DLL (bulk-decrypted)" %}
Key observations in this trace:

* **`A11` -> `5D0` -> `A15`:** `A11` verifies that the host EXE carries CrackProof host markers; `A15` is emitted after `5D0` as a pure DLL sequencer marker confirming host verification passed.
* **No `640` / `840` (`-NCP`):** sections decrypt once at `610`, relocate at `655`, and step through `800 -> 830 -> 280` with all code pages left resident in memory.

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
Key observations in this trace:

* Runs the minimal CLR DLL sequence: `510` loader CRC, `A09` VM registry check, `A11` host-EXE check, decrypt prelude `5D0..5A0`, section/method-body decryption at `610`, and immediate handoff at `280` (no driver init, relocations, or page sealing).

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
