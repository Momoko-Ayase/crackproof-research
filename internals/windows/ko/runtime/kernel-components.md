---
description: "Htsysm 커널 드라이버 1~3세대 구조: 셸코드 실행, EPROCESS 수정, 콜백."
icon: gears
---

# Htsysm 커널 구성 요소

CrackProof의 선택적 커널 계층(`Htsysm`)은 3세대에 걸친 드라이버 아키텍처로 발전해 왔습니다.

{% tabs %}
{% tab title="1세대: HtsysmNT" %}
### 인증 없는 커널 셸코드 실행

1세대 드라이버는 호출자 인증 없이 전달받은 Ring-0 셸코드를 그대로 실행하는 IOCTL을 노출합니다. CrackProof의 유저모드 `cm` 보조 모듈은 이 기능을 이용해 커널 모드 DLL 두 개(`B21` 단계의 `HtsyskNT.dll`, `BB0` 단계의 `HtpecmNT.dll`)를 커널 공간에 수동 매핑하고 `_FarEntry@0` 익스포트를 호출해 커널 메모리 접근과 프로세스 종료를 수행합니다. 로컬 유저모드 프로세스라면 어느 프로세스든 동일한 IOCTL을 호출할 수 있으므로, 이 드라이버가 설치된 시스템에서는 임의의 Ring-0 코드 실행이 가능해집니다.
{% endtab %}

{% tab title="2세대: Htsysm7679" %}
### 범위 제한 `EPROCESS` 마스크 DWORD 수정 (`0xAA01`)

2세대(`Htsysm7679`, 디바이스 타입 `0xAA01`, IOCTL `0xAA013880` / `0xAA013884` / `0xAA013888`)는 범용 셸코드 실행 기능을 제거하고, 대신 부호 없는 `offset < 0x1000` 범위 내에서 `IoGetCurrentProcess() + offset`에 대해 32비트 마스크 기반 비트 해제, 설정, 읽기 연산만 수행합니다.

* **보호 프로세스(`PP`) 토글:** 로더는 `C03`/`C04` 단계에서 현재 프로세스의 `EPROCESS` 내 보호 프로세스 비트필드를 설정해 유저모드 디버거나 인젝터가 전체 권한 핸들을 열지 못하도록 차단합니다. 다만 `PP`가 활성화되면 `NtCreateSection` 등 일부 Win32/NT 호출이 실패하므로, 유저모드 로더가 해당 함수들을 후킹해(`C04`에서 기록) 호출 직전에 `PP`를 해제하고 원본 API를 실행한 뒤 다시 `PP`를 설정합니다.
* **BYOVD 노출:** 호출자 검증이 역연산 가능한 PID 기반 암호에만 의존하므로, 이 PID 변환을 재현한 로컬 프로세스는 자신의 `EPROCESS`(`offset < 0x1000`) 내 필드를 수정하거나 `C04` 단계에서 `PP`가 활성화되기 전에 대상 프로세스에 인젝션할 수 있습니다.
{% endtab %}

{% tab title="3세대: Htsysm767901 및 Htsysm1B4001" %}
### `ObRegisterCallbacks` 핸들 권한 제거 (`0xAA02`)

3세대(`Htsysm767901` 및 `Htsysm1B4001`, 디바이스 타입 `0xAA02`, `0xAA023800..0xAA02382C`의 12개 IOCTL)는 `EPROCESS` 직접 수정을 완전히 제거하고 객체 관리자 콜백(`ObRegisterCallbacks`, `Htsysm1B4001`의 경우 `1B4001`에서 유도된 `Altitude` 값 `88180.011104000001` 사용)을 등록해 최대 100개의 보호 프로세스와 12개 항목의 텔레메트리 링 버퍼를 관리합니다.

* **핸들 권한 제거 마스크 (`& 0xFFFFFFC5`, `0x3A` 비트 제거):** 승인되지 않은 핸들 열기 및 복제 요청에서 `PROCESS_CREATE_THREAD`(`0x02`), `PROCESS_VM_OPERATION`(`0x08`), `PROCESS_VM_READ`(`0x10`), `PROCESS_VM_WRITE`(`0x20`) 권한을 제거합니다.
* **예외 허용 규칙:** `KernelHandle`, 자기 자신에 대한 접근, 설정된 호출자 PID 최대 5개(`0xAA02380C`), 설정된 호출자 부모 PID 최대 3개(`0xAA023810`)를 허용하며, `csrss.exe`, `lsass.exe`, `conhost.exe`, `svchost.exe`는 **설정된 시스템 디렉터리에서 실행 중인 경우에만** 허용합니다(`0xAA023800`, `svchost.exe`는 예상 부모 PID `0xAA023814` 조건 추가).
* **3단계 핸드셰이크:** 등록 과정은 고정된 PID 암호 대신 자체 코드 해시와 반환 주소 해시를 사용하며, 유저모드 호출자에게 커널 메모리 쓰기 기능을 제공하지 않습니다.
{% endtab %}
{% endtabs %}

## 버전 스탬프 (`0x7679` 및 `1B40`)

`Htsysm7679` 및 `Htsysm767901`에 포함된 `0x00007679`는 PE32 `EighthStage`와 Stage 5 마커 테이블에 나타나는 `0x00007679` 설정 클러스터 스탬프와 일치합니다([PE32, DLL 및 마커 없는 레이아웃](../loading-and-pe-repair/loading/layout-variants.md) 참고). `C02`/`C03`에서 `Htsysm1B4001`을 기록하는 최신 Windows 빌드는 Android 빌드에서도 확인되는 `1B40` 스탬프를 공유하며, 3세대 `0xAA02` 콜백 드라이버를 사용해 `C04` 단계에서 필요한 유저모드 API 후킹 수를 줄이며 `E` 계열 디바이스 검사(`E55`, `E91`)를 함께 활성화하는 경우가 많습니다.

## 요약 표

| 구성 요소 | 계층 | 역할 |
| --- | --- | --- |
| `HtpecIt.dll` (`it`) | 수동 매핑 유저모드 DLL | `Axx` 변조 탐지, 인젝션, VM 및 호스트 검사 |
| `HtdpStub2.dll` (`dt`) | 수동 매핑 유저모드 DLL | 온디맨드 페이지 복호화 예외 핸들러 및 페이지 테이블 |
| `HtsyskNT.dll` (`sk`) / `HtpecmNT.dll` (`pm`) | 1세대 커널 DLL | 커널 수동 매퍼(`B21`) 및 프로세스 모니터(`BB0`) |
| `HtsysmNT` | 커널 드라이버 (1세대) | 인증 없는 Ring-0 셸코드 실행 |
| `Htsysm7679` | 커널 드라이버 (2세대, `0xAA01`) | 현재 `EPROCESS`의 범위 제한(`offset < 0x1000`) 마스크 DWORD 수정 |
| `Htsysm767901` / `Htsysm1B4001` | 커널 드라이버 (3세대, `0xAA02`) | 경로 및 PID 예외 조건을 갖춘 `ObRegisterCallbacks` 핸들 권한 제거 |
