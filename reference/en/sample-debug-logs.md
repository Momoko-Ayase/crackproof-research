---
description: "Desensitized debug logs from protected host, native DLL, and managed DLL samples."
---

# Sample debug logs

These are genuine CrackProof debug logs, captured by creating the per-executable 12-hex-character folder under `%temp%` and launching a protected title (see [Debug logging](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/runtime/startup-status#debug-logging)). Paths and product names are replaced with generic placeholders; everything else — option flags, status codes, addresses, hook lists — is verbatim.

## Reading a log

* **Line 1** — the protected module's path.
* **Line 2** — the protection option flags the build was packed with (each `-XX` token is one packer option).
* **Line 3/4** — timestamp and the module's load base.
* **Following lines** — 12-bit [status codes](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/runtime/startup-status#the-boot-sequence-and-status-codes), one per stage; indented `000`– `00N` lines carry stage-specific detail (addresses, counts, hooked functions).
* **Final lines** — completion timestamp and the 9-digit error code (`000-000-000` = success).

## Host EXE — fully featured, page-encrypted

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

Points of interest:

* `C03` names the driver generation: `Htsysm7679` — the second-generation Htsysm (see [Htsysm kernel components](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/runtime/kernel-components)).
* `C04` lists every API hooked for the Protected-Process toggle (`NtCreateSection`, `NtAlpcSendWaitReceivePort`, `NtDuplicateObject`, `NtConnectPort`, `NtOpenProcess`, `NtOpenThread`, …) plus loader-interception hooks (`CreateProcessInternal*`, `CreateRemoteThread*`, `LdrLoadDll`, `CreateActCtxW`).
* `640 … 840` — this module is **page-encrypted**: bulk decrypt, then re-encrypt with the exception-handler hook installed. The `002` line after `840` carries three addresses (the re-encrypted range and handler data).
* `570` and `A06` hook additional APIs late in the boot (`user32!SetFocus`, `CreateWindowExA/W`, `uxtheme!ThemeInitApiHook`).
* `660` is a stage not in the public status table — present here between `840` and the final `280` (jump to OEP).

## Native plugin DLL — bulk-decrypted only

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

Points of interest:

* `A11` — the DLL host-process check, present only for protected DLLs.
* **No `640`/`840`** — this build is bulk-decrypted once (`610`) and never page-encrypted; compare the host EXE above. Page encryption is a per-module option.
* `800` carries a single address — the freshly populated image region.

## Managed DLL — minimal sequence

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

The managed build runs the shortest pipeline: environment checks, section decryption (`610`), then straight to the OEP (`280`) — no driver init, no page encryption, no relocation stage.
