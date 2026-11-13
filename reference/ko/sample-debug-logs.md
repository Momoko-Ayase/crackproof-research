---
description: "페이지 암호화 호스트 EXE, 네이티브 플러그인 DLL, 관리형 DLL의 익명화 런타임 로그."
icon: file-lines
---

# 샘플 디버그 로그

실행 전 `%temp%` 아래에 각 바이너리의 12자리 16진수 폴더를 생성하여 수집한 실제 CrackProof 런타임 로그입니다([디버그 로깅](https://app.gitbook.com/s/XSPACE_WINDOWS_KO/runtime/startup-status#debug-logging) 참고). 파일 경로와 제품명은 일반 자리표시자로 치환했으며, 옵션 플래그, 상태 코드, 주소 및 후킹된 API 목록은 원문 그대로 유지했습니다.

## 로그 구조

* **1행:** 보호된 EXE 또는 DLL의 전체 경로입니다.
* **2행:** 모듈 빌드 시 기록된 패커 옵션 토큰(`-CF`, `-CP`, `-PP` 등)입니다.
* **3행 및 4행:** 시작 타임스탬프와 16진수 모듈 로드 베이스 주소입니다.
* **본문 행:** 12비트 [상태 코드](https://app.gitbook.com/s/XSPACE_WINDOWS_KO/runtime/startup-status#the-boot-sequence-and-status-codes)와 들여쓰기된 `000`..`00D` 상세 행으로 구성되며, 단계 파라미터, 드라이버 이름, 후킹된 함수 주소를 기록합니다.
* **마지막 행:** 종료 타임스탬프와 `AAA-BBB-CCC` 결과 코드입니다(정상 시작 시 `000-000-000`).

## 수집된 로그 전문

{% tabs %}
{% tab title="호스트 EXE (페이지 암호화)" %}
이 트레이스의 주요 관찰 사항은 다음과 같습니다.

* **`C00` (`01A065F4 01A037AB`):** 각 dword 값은 `0x01A00000 + build` 형식이며, 호스트 Windows 빌드 번호인 `26100` (`0x65F4`) 및 최소 허용 빌드 번호인 `14251` (`0x37AB`) 값을 기록합니다.
* **`C03` 및 `C04`:** 2세대 드라이버 `Htsysm7679`를 초기화하고([Htsysm 커널 구성 요소](https://app.gitbook.com/s/XSPACE_WINDOWS_KO/runtime/kernel-components) 참고), 호환되지 않는 시스템 호출 전후에 보호된 프로세스(Protected Process) 상태를 전환하기 위해 `kernel32` / `kernelbase` / `ntdll` API 15개를 후킹합니다.
* **`610 -> 640 -> 655 -> 6E1 -> 800..840 -> 660 -> 280`:** 실행 섹션을 일괄 복호화(`640`)하고 재배치를 적용(`655`)한 뒤, `KiUserExceptionDispatcher`를 후킹하고 실행 페이지를 `PAGE_NOACCESS`로 전환합니다(`840`). 이어서 페이지 보호 설정 후 인계 단계(`660`)를 실행하고 OEP로 점프합니다(`280`).

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

{% tab title="네이티브 플러그인 DLL (일괄 복호화)" %}
이 트레이스의 주요 관찰 사항은 다음과 같습니다.

* **`A11` -> `5D0` -> `A15`:** `A11`은 호스트 EXE에 CrackProof 호스트 마커가 있는지 검증하며, `A15`는 호스트 검증 통과를 나타내는 순수 DLL 시퀀서 마커로 `5D0` 이후에 기록됩니다.
* **`640` / `840` 없음 (`-NCP`):** 섹션을 `610`에서 한 번만 복호화하고 `655`에서 재배치한 뒤, 모든 코드 페이지를 복호화된 상태로 둔 채 `800 -> 830 -> 280` 순서로 진행합니다.

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

{% tab title="관리형 DLL" %}
이 트레이스의 주요 관찰 사항은 다음과 같습니다.

* 로더 CRC 검사(`510`), VM 레지스트리 검사(`A09`), 호스트 EXE 검사(`A11`), 복호화 준비 단계(`5D0..5A0`), 섹션 및 메서드 본문 복호화(`610`), 즉시 제어권 전환(`280`)으로 이어지는 최소한의 CLR DLL 시퀀스만 실행합니다(드라이버 초기화, 재배치, 페이지 암호화 없음).

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
