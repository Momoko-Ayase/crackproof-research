---
description: "CLI protect, inspect, verify 명령과 프로필, 환경 검사 및 디버그 로그."
icon: terminal
---

# 사용법

`arare-cli`를 빌드하면 Senbei 체크아웃 없이도 `target/release/arare.exe`가 생성됩니다. 관리형 어셈블리 패킹에는 추가로 .NET 10 런타임과 관리형 도구 파일 3개(`Arare.ManagedHost.dll`, `Arare.ManagedHost.runtimeconfig.json`, `Arare.Bootstrap.dll`)가 필요하며, 이 파일들을 `arare.exe` 옆의 `managed/` 폴더에 두거나 `ARARE_MANAGED_TOOLS` 환경 변수로 경로를 지정해야 합니다([개발](development.md) 참고). 배치 GUI 사용법은 [GUI](gui.md)에서 다룹니다.

```text
arare protect INPUT -o|--output OUTPUT --profile PROFILE
    [--seed 64_HEX_DIGITS] [--no-compression]
    [--storage embedded|companion] [--check NAME=on|off]...
    [--page-encrypt on|off] [--scribble on|off]
    [--errlog on|off] [--antidebug-av on|off]
    [--force] [--json]

arare inspect INPUT [--json]

arare verify INPUT --profile PROFILE [--companion PATH] [--json]
```

## 프로필 및 저장 방식

| 프로필 | 대상 레이아웃 계열 |
| --- | --- |
| `pe32` | PE32 x86 네이티브 이미지 및 지원되는 x86/AnyCPU 관리형 어셈블리 |
| `pe64-classic` | 마커 기반 EXE 스타일의 클래식 PE32+ x64 EXE 및 DLL |
| `pe64-modern` | 마커 없는 EXE 스타일의 PE32+ x64 EXE 및 DLL |
| `legacy-dll` | 구형 전용 PE32+ x64 DLL 레이아웃 (내장 저장 방식만 지원) |

프로필 이름은 상용 제품 버전이 아니라 구조적 레이아웃 계열을 식별합니다. 입력 제약 사항은 [지원 범위](support.md)를 참고하십시오.

* **컴패니언 저장 방식 (`--storage companion`):** 4 KiB 헤더/오버레이 스텁인 `OUTPUT` 파일과 `0x1000..0x1020` 구간의 32바이트 헤더로 연결되는 암호화 페이로드인 `<OUTPUT>._` 파일을 모두 생성합니다. 두 파일은 같은 폴더에 유지해야 합니다.
* **시드 및 압축:** `--seed`를 생략하면 Windows CSPRNG에서 무작위 32바이트를 추출하고 해당 16진수 시드를 출력합니다. `--no-compression`은 로더 단계 인코딩은 그대로 유지하면서 애플리케이션 섹션 블록만 압축하지 않고 저장합니다.
* **정적 검증 (`verify`):** 대상 바이너리를 실행하지 않고 Arare의 독립 네이티브 디코더로 보호된 파일을 디코딩하여 검증합니다. `--companion`을 생략하면 32바이트 헤더가 일치하는 `<INPUT>._` 컴패니언 파일을 자동으로 찾아 결합합니다.

## 환경 검사 및 실패 시 동작

보호된 모듈은 시작 과정에서 3단계에 걸쳐 설정 가능한 환경 검사를 수행합니다(파일 스테이징 전 1단계, 스테이징 후 2단계, 페이지 보호 설정 후 3단계). 기본값을 변경하려면 `--check NAME=on|off` 플래그를 반복 지정합니다.

| 모듈 유형 | 기본 활성화 검사 |
| --- | --- |
| 네이티브 EXE | `antidebug`, `crc-loader`, `debug-port`, `os-version`, `boot-options`, `vm-registry`, `injected-dll`, `injected-thread`, `clean-code` |
| 네이티브 DLL | `crc-loader`, `vm-registry`, `host-process` |
| 관리형 EXE | `crc-loader`, `vm-registry` |
| 관리형 DLL | `crc-loader`, `vm-registry`, `host-process` |

두 DLL 유형 모두 `host-process` 기본값이 `on`이므로 보호되지 않은 일반 호스트 프로세스에서 보호된 DLL을 로드하려면 `--check host-process=off`를 지정해야 합니다. `vm-backdoor`, `parent-process`, `hyperv-guest`는 모든 모듈 유형에서 기본값이 `off`입니다.

| CLI 검사 이름 | 단계 코드 | 동작 |
| --- | --- | --- |
| `antidebug` | `410` | 7개 세부 단계: `IsDebuggerPresent`, `PEB.BeingDebugged`, `PEB.NtGlobalFlag & 0x70`, 하드웨어 디버그 레지스터 `DR0`..`DR3` / `DR7 & 0xFF` (`GetThreadContext`), `NtQueryInformationProcess` (`ProcessDebugPort`, `ProcessDebugFlags == 0`, `ProcessDebugObjectHandle`) |
| `crc-loader` | `510` | 로더 코드 CRC-32 자체 무결성 검사 |
| `debug-port` | `520` | 커널 디버그 포트 조회 |
| `kernel-debugger` | `52F` | `KdDebuggerEnabled` 및 시스템 커널 디버거 검사 |
| `vm-backdoor` | `540` | VMware `0x5658` I/O 포트 프로브 (일반 CPUID 하이퍼바이저 비트는 무시하며 Hyper-V/VBS 허용) |
| `hyperv-guest` | `541` | Arare 전용 Hyper-V 게스트 파티션 권한 검사 (`Hv#1` CPUID) |
| `parent-process` | `A03` | 부모 프로세스가 `explorer.exe` 또는 `cmd.exe`가 아니면 거부 |
| `os-version` | `C00` | Windows 10 빌드 `10240` 이상 요구 |
| `boot-options` | `C01` | 테스트 서명(test-signing) 및 디버그 부팅 플래그 거부 |
| `msc-log` | `BD0` | `C:\Windows\msc.log.log` 파일이 존재하면 거부 |
| `os-compat` | `B00` | OS 호환성 게이트 검사 |
| `vm-registry` | `A09` | 시스템 하드웨어/BIOS VM 레지스트리 마커 검사 (`Hv#1`이 Hyper-V/VBS를 나타내면 일반 `Virtual` / `VRTUAL` / `Microsoft Hyper-V` 항목 허용) |
| `injected-dll` | `A0F` | OEP 진입 전 로드된 모듈 스캔 |
| `injected-thread` | `A07` / `A01` | 예기치 않은 외부 주입 스레드 탐지 |
| `host-process` | `A11` | 호환되는 Arare EXE 호스트 요구 (`.arldr` 또는 `.armclr` 마커 확인) |
| `host-stamp` | `A11` | `host-process=on`일 때 선택적으로 수행하는 협력형 런타임 컨텍스트 스탬프 검사 |
| `clean-code` | `A08` | 변조되지 않은 시스템 DLL 바이트를 통해 로더 호출 라우팅 |
| `disk-integrity` | `A04` | 두 옵션을 모두 요청하더라도 `clean-code`를 대체하며, 메모리에 매핑된 시스템 DLL을 디스크의 시스템 이미지와 대조 |
| `legacy-debugger` | `BE0` | 레거시 디버거 디바이스 프로브 |
| `openark-device` | `E55` | 페이지 보호 설정 후 OpenArk 드라이버 디바이스 검사 |
| `cheat-engine-device` | `E91` | 페이지 보호 설정 후 Cheat Engine 드라이버 디바이스 검사 |

{% hint style="warning" %}
**꼭 필요한 경우가 아니면 `hyperv-guest`를 활성화하지 마십시오.** `--check hyperv-guest=on`은 루트/호스트 VBS 파티션은 허용하면서 `Hv#1` CPUID 파티션 권한으로 식별되는 게스트 VM만 차단합니다. 하이퍼바이저 CPUID 리프는 마스킹하거나 스푸핑할 수 있으므로 `hyperv-guest`는 변조 방지 수단이 아니라 실행 환경 제한 용도로만 사용하십시오.
{% endhint %}

**검사 실패 시 동작 (`--antidebug-av`):** `--antidebug-av`는 EXE에서 기본값 `on`, DLL에서 기본값 `off`로 동작합니다(네이티브 모듈 로그에는 `-AV=ON` / `-AV=OFF`로 기록됨). `--antidebug-av=on`이 활성화된 네이티브 모듈에서 검사가 실패하면 런타임이 로그를 닫고 `RaiseException(0xC0000005)`(`EXCEPTION_ACCESS_VIOLATION`) 호출과 널 포인터 쓰기를 수행한 뒤 `TerminateProcess(0xE0A00000 | substage)`를 호출하므로 연결된 디버거가 즉시 중단됩니다. `--antidebug-av=off`가 지정된 네이티브 모듈과 관리형 모듈은 곧바로 `TerminateProcess`를 호출합니다.

## 페이지 암호화

`--page-encrypt` 기본값은 EXE에서 `on`, DLL에서 `off`입니다. 섹션 재구성이 끝나면 런타임이 실행 가능한 애플리케이션 페이지를 제자리에서 다시 암호화해 보호 속성을 `PAGE_NOACCESS`로 전환하고, `ntdll!KiUserExceptionDispatcher`를 후킹하여 첫 실행 시 접근 위반 예외가 발생하면 해당 페이지를 온디맨드로 복호화합니다. 쓰기 및 실행이 동시에 허용된(`RWX`) 섹션이 있거나 섹션 정렬값이 `0x1000` 미만인 입력은 페이지 암호화 활성화 시 패킹이 거부됩니다.

`--scribble=on`(기본값 `off`, `--page-encrypt=on` 필요)을 지정하면 접근 위반 예외 처리 사이에 이미 복호화된 페이지의 일부 바이트를 마스킹합니다.

## 디버그 로그 및 `ErrLog-Pec`

`protect --json`(및 표준 콘솔 출력)은 모듈의 12자리 16진수 `log_folder` 값을 출력합니다. `%TEMP%\<log_folder>` 폴더가 존재하고 생성된 지 48시간 미만이면 모듈은 시작 시 런타임 상태 로그(EXE는 `HHMMSSmmmE-...`, DLL은 `HHMMSSmmmD-...`)를 기록하고 마지막에 `AAA-BBB-CCC` 종료 요약 코드를 남깁니다.

{% hint style="info" %}
**DLL 로그 게이트 상속.** 보호된 Arare EXE 프로세스 내부에 보호된 DLL이 로드되면 시드가 다르거나 `host-process=off`가 설정되어 있더라도 항상 호스트 EXE의 로깅 컨텍스트를 따릅니다. EXE의 `%TEMP%` 폴더가 없거나 생성된 지 48시간이 지났다면 DLL 자체의 대체 `log_folder`가 존재하더라도 로그를 기록하지 않습니다.
{% endhint %}

`--errlog=on`(기본값 `off`)을 지정하면 `%TEMP%` 폴더 게이트와 무관하게 타임스탬프, `AAA-BBB-CCC` 코드, 모듈 및 OS 정보를 담은 종료 진단 패킷을 `\\.\mailslot\ErrLog-Pec<suffix>`로 전송합니다(여기서 `<suffix>`는 `((key + 1) * 0x3039) % 0x8003`으로 계산한 4자리 16진수 값).

## 출력 파일 기록 및 JSON 리포트

모든 출력 데이터는 메모리상에서 완전히 인코딩한 뒤 스테이징 파일에 기록하고 플러시한 다음 원자적(atomic)으로 이름을 변경합니다(기존 파일을 덮어쓰려면 `--force` 필요). 입력 파일을 가리키는 심볼릭 링크나 정규 경로 별칭으로 출력하는 작업은 거부되며, 별도의 하드 링크 엔트리를 교체할 때는 원본 입력 바이트가 그대로 보존됩니다.

<details>
<summary>JSON 출력 필드 (protect, inspect, verify)</summary>

* **`protect --json`:** `output`, `profile`, `storage`, `architecture`, `module`, `input_size`, `output_size`, `seed`, `normalizations`, `log_folder`, `companion`, `companion_size`.
* **`inspect --json`:** `architecture`, `module`, `entry_point`, `image_base`, `image_size`, `file_size`, `sections` (`name`, `rva`, `virtual_size`, `raw_offset`, `raw_size`, `characteristics`).
* **`verify --json`:** `valid`, `profile`, `companion`, `image_size`, `recovered_file_size`, `entry_point`.
</details>
