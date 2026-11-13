---
description: "HtdpsCmnGetFileInfo를 통해 수동 매핑되는 내장 보조 DLL 카탈로그."
icon: layer-group
---

# 수동 매핑 보조 모듈

CrackProof는 주요 런타임 서브시스템을 보호 대상 바이너리 자체 섹션에 노출하지 않기 위해 보조 DLL을 로더 페이로드 내부에 포함하고, 두 글자 모듈 코드를 키로 사용하는 내부 로더(`HtdpsCmnGetFileInfo`)를 통해 메모리에 수동 매핑합니다.

## 서브모듈 카탈로그

`HtdpsCmnGetFileInfo`는 요청된 보조 DLL을 전용 실행 메모리에 수동 매핑하여 `InLoadOrderModuleList`나 `CreateToolhelp32Snapshot`이 순회하는 `PEB` 로더 모듈 목록에 나타나지 않게 하며, PE 헤더에서 엔트리 포인트를 계산한 뒤 `MZ` 및 `PE\0\0` 시그니처를 0으로 지울 수 있습니다.

| 2글자 코드 | 모듈 이름 | 상태 코드 범위 | 런타임 역할 |
| --- | --- | --- | --- |
| `it` | `HtpecIt.dll` | `Axx` | 유저모드 변조 탐지, 인젝션 탐지, VM 레지스트리 및 호스트 프로세스 검사 |
| `dt` | `HtdpStub2.dll` | `8xx` / 예외 발생 시 | 온디맨드 페이지 복호화 예외 핸들러 (`KiUserExceptionDispatcher` 점프 대상) 및 페이지별 테이블 |
| `cm` | (유저모드 보조 모듈) | `Bxx` | 1세대 `Htsysm` 드라이버 설정 |
| `dm` | (유저모드 보조 모듈) | `Cxx` | 2세대 및 3세대 `Htsysm` 드라이버 설정 및 IOCTL 핸드셰이크 |
| `sk` | `HtsyskNT.dll` | `B21` | 1세대 커널 DLL: 커널 수동 매퍼 및 메모리/I/O 기본 루틴 |
| `pm` | `HtpecmNT.dll` | `BB0` | 1세대 커널 DLL: 프로세스 모니터링 및 강제 종료 |

온디맨드 페이지 복호화 루틴과 영역 및 페이지 디스크립터 배열이 모두 `dt`(`HtdpStub2.dll`) 내부에 포함되어 있으므로([페이지 보호 및 로더 코드](page-protection.md) 참고), 메인 `.exe`나 `.dll` 모듈만 덤프하면 온디맨드 페이지 복호화 핸들러가 통째로 누락됩니다. `dt` 모듈을 확보하려면 실행 권한이 있는 전용(`MEM_PRIVATE`) VAD 영역을 탐색하거나 `ntdll!KiUserExceptionDispatcher` 시작부의 인라인 점프를 따라가야 합니다. 이에 대응하는 커널 측 구성 요소는 [Htsysm 커널 구성 요소](kernel-components.md)에서 다룹니다.
