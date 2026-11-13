---
description: "런타임 디버거, VM, 시스템 무결성, 인젝션, A11/A15 호스트 및 언후킹 검사."
icon: user-shield
---

# 환경 및 안티분석 검사

CrackProof의 시작 검사는 1단계(페이로드 준비 이전), `C`/`B`/`A` 시퀀서 패스, 그리고 페이지 보호 설정 이후 선택적으로 수행되는 `E` 계열 검사에 걸쳐 실행됩니다.

{% tabs %}
{% tab title="디버거" %}
* **`410` (유저모드 안티디버깅):** `IsDebuggerPresent`를 확인합니다. 실제 캡처 결과 상용 `410` 내부에는 SEH 기반 하위 단계가 없으며, 트랩 플래그(`#DB`) SEH 디코이는 Stage 5 로더 코드에 별도로 존재합니다.
* **`520` 및 `52F`:** `NtQueryInformationProcess`의 디버그 관련 정보 클래스(`520`)와 커널 디버거 활성화 상태(`52F`)를 조회합니다.
* **`BE0`:** 구형 SoftICE 및 Syser 드라이버 디바이스 이름을 검사합니다.
* **타이밍 및 `#DB` 디코이:** Stage 5 코드 곳곳에 `in eax, dx` 타이밍 읽기와 `pushfq; or [rsp], 0x100; popfq` 싱글스텝 트랩이 배치되어 있으며, 정상 실행 시 SEH 핸들러가 더미 경로를 건너뜁니다([페이지 보호 및 로더 코드](page-protection.md) 참고).
{% endtab %}

{% tab title="가상 머신" %}
* **`540` (VMware 백도어):** `0x5658` I/O 포트 프로브(`in eax, dx`)를 실행합니다. 베어메탈 환경이나 비 VMware 하이퍼바이저에서는 `#GP` 예외가 발생하는 반면, VMware 환경에서는 매직 데이터가 반환됩니다.
* **`A09` (하드웨어 레지스트리 접두사):** `HKLM\Hardware\Description\System\SystemBiosVersion`, `HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation\SystemProductName`, `HKLM\Hardware\Description\System\BIOS\SystemProductName` 값의 앞부분이 `Virtual`, `VMware`, `Bochs`, `VBOX`, `VRTUAL`, `Microsoft Hyper-V`, `Parallels` 접두사로 시작하는지 확인합니다(일부 빌드는 이 단계에서 CPU 가상화 기능 비트도 함께 검사합니다).
{% endtab %}

{% tab title="시스템 무결성" %}
* **`C00` 및 `B00`:** 실제 OS 빌드 값(`0x01A00000 + build`)을 설정된 Windows 10 이상 최소 빌드 기준값과 비교하고(`C00`, 보고되는 빌드 번호만 낮추는 단순 PEB 버전 스푸핑을 무력화함), OS 호환성을 확인합니다(`B00`).
* **`C01`:** `testsigning` 또는 `disableintegritychecks` 부팅 옵션이 활성화된 시스템을 거부합니다.
* **`BD0`:** `C:\Windows\msc.log.log` 파일이 존재하면 실행을 중단합니다.
* **`E55` 및 `E91`:** `1B40` 계열 빌드에서 OpenArk, Cheat Engine 등 분석 도구 드라이버와 연결된 심볼릭 디바이스 링크를 탐지합니다.
{% endtab %}

{% tab title="프로세스 및 호스트 (A11 / A15)" %}
* **`A03`:** 부모 프로세스 이름을 제한합니다(일반적으로 `explorer.exe` 또는 `cmd.exe`만 허용).
* **`A0F`:** 로드된 모듈 목록(`AppInit_DLLs`, `user32.dll`, `apphelp.dll`, `ShimEng.dll` 포함)을 스캔하며, 일부 호스트 빌드에서는 애플리케이션 디렉터리 내 예상치 못한 DLL도 거부합니다.
* **`A07` 및 `A01`:** 예상치 못한 외부 스레드를 강제 종료하고(`A07`), 종료되지 않고 남아 있는 외부 스레드가 있으면 실행을 중단합니다(`A01`).
* **`A11` (DLL 호스트 검증):** 현재 프로세스에 매핑된 호스트 EXE를 검사해 `peC`라는 이름의 섹션이 있거나 대소문자가 정확히 일치하는 `KeRnEl32.dLl` 임포트 디스크립터가 있는지 확인합니다(Windows 로더는 대소문자를 구분하지 않고 DLL을 해석하지만, 대소문자 혼합 문자열 자체가 CrackProof 호스트임을 나타내는 표식 역할을 합니다). 두 번째 `A11` 변형은 추가 플래그 매개변수를 함께 검사합니다.
* **`A15` (DLL 시퀀서 마커):** 별도의 검사 로직이 없으며, 보호된 DLL 패스에서 `A09`/`A11` 통과 후 `5D0` 다음에 기록됩니다. 호스트 EXE는 `A15`를 기록하지 않고 해당 위치에서 `552`/`570`을 기록합니다.
{% endtab %}

{% tab title="안티후킹" %}
* **`A08` 및 `A04`:** `System32`에 있는 원본 `ntdll.dll`과 `kernel32.dll`을 디스크에서 매핑한 뒤 메모리의 `.text` 영역을 원본 바이트로 덮어써 유저모드 인라인 후킹을 제거합니다. 또한 `A04`는 디스크 상의 시스템 DLL 파일 자체가 변조된 경우 실행을 중단합니다.
{% endtab %}
{% endtabs %}
