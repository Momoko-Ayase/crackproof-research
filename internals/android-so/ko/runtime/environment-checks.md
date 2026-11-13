---
description: "Android의 NativeBridge, ptrace, 메모리 감시 및 APK 서명 검사"
icon: user-shield
---

# 환경 및 무결성 검사

Windows 제품군과 달리 Android용 CrackProof는 커널 드라이버 없이 유저모드에서만 동작합니다. 환경 및 무결성 검사는 중첩 스트림을 언패킹하는 동안 Stage 1, Stage 2와 [런타임 모듈](modules.md)에 정리된 작업 모듈 전반에서 실행됩니다.

## 프로세스 및 ABI 변환 검사

* **자체 매핑 및 환경 변수 확인:** Stage 1은 원본 ELF 파일을 찾기 위해 `/proc/self/maps`를 파싱하며, Stage 2는 매핑 컨텍스트를 유지한 채 `/proc/self/environ`을 검사합니다.
* **x86 상의 ARM 바이너리 변환(`NativeBridge`):** 네이티브 AArch64 실행 환경이 아닌 x86 상의 ARM 변환 계층을 탐지하기 위해 `/system/lib/libhoudini.so`와 `/system/lib64/arm64/nb/` 경로의 존재 여부를 확인합니다.
* **파일시스템 및 `libc` 검사:** 모듈 `0x8F`는 `/proc/self/cmdline`, `uid`/`gid`/`tid`, 파일 소유권 및 권한을 점검합니다. 모듈 `0x60`은 시스템 라이브러리 디렉터리와 런타임 경로를 스캔하고, 모듈 `0x20`은 대상 ELF 헤더, `/proc/self/maps`, 활성 `libc` 매핑을 검증합니다.

## 보조 프로세스와 `PTRACE_SEIZE`

확인된 IL2CPP 빌드는 ART와 VM 라이브러리가 초기화된 직후, `dlopen`으로 보호된 `.so`를 로드하기 전에 보조 프로세스를 `fork`합니다. 자식 프로세스는 `PTRACE_SEIZE | PTRACE_O_EXITKILL` 플래그로 부모 프로세스에 어태치하여 커널의 `ptrace` 슬롯을 선점하며, 어느 한쪽 프로세스가 종료되면 앱 전체가 함께 종료되도록 묶습니다. 보호된 `.so`가 로드되기 전에 `fork`하므로 `/proc/<child>/maps`에는 해당 공유 라이브러리가 나타나지 않습니다.

## `/proc/<pid>/mem` 감시와 페이지 권한

확인된 빌드에서 `/proc/<pid>/mem`을 열어 읽으면 수 초 내에 프로세스가 종료됩니다. 반면 `/proc/<pid>/maps`, `cmdline`, `status`를 읽거나 `process_vm_readv`로 메모리를 읽어도 프로세스가 종료되지 않았습니다. 또한 `0x9B`가 세그먼트 복원을 마치면 실행 페이지는 읽기 가능 상태(`PROT_READ | PROT_EXEC`)로 유지되며, Android 빌드는 `PAGE_NOACCESS` 폴트 기반의 온디맨드 페이지 암호화를 적용하지 않습니다.

## APK 서명 및 네트워크 시간 검증

모듈 `0x40`은 APK 서명 스킴 v3.1, v3, v2, JAR 서명(v1) 순으로 내려가며 `base.apk`와 분할 APK(split APK)의 서명을 검증합니다. 모듈 `0x02`는 UDP 123번 포트로 NTP 서버에 질의하여 반환된 타임스탬프를 설정된 기준 범위와 비교하며, 모듈 `0x69`는 짧게 실행되는 검사용 자식 프로세스를 생성한 뒤 종료 상태(`wait` status)를 확인합니다.

## 링커 모듈 목록 미노출

Stage 2 인터프리터와 작업 모듈은 익명 `mmap` 영역(초기화 중에는 주로 `RWX` 권한)에 상주하며, 콜백 실행을 마친 뒤 자신의 메모리 영역을 0으로 지우거나 덮어쓸 수 있습니다. Windows의 [수동 매핑 보조 DLL](https://app.gitbook.com/s/XSPACE_WINDOWS_KO/runtime/mapped-modules)과 마찬가지로, 이 모듈들은 Bionic 링커의 `dl_iterate_phdr`이나 `soinfo` 목록에 나타나지 않습니다.
