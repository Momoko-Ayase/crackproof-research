---
description: "Android ELF64, 암호, Stage 2 모듈, 재배치 및 IL2CPP 주요 상수"
icon: sliders
---

# 상수

아래 표는 분석된 CrackProof Android AArch64 빌드 전반에서 확인된 포맷 상수를 정리한 것입니다. 실제 판별과 복원에서는 단일 상수 값보다 구조적 경계 검사와 테이블 간 교차 검증이 우선합니다.

## ELF 및 Stage 1

| 상수 | 적용 범위 |
| --- | --- |
| ELF64, 리틀 엔디언, `EM_AARCH64`(`183` / `0xB7`) | 필수 파일 클래스, 엔디언 및 아키텍처(`e_phentsize = 0x38`, `e_shentsize = 0x40`) |
| `SHT_LOUSER`(`0x80000000`) | 파일 기반 `PT_LOAD` 끝의 16바이트 정렬 오프셋에 붙는 단일 전용 페이로드 섹션 |
| `0x84`바이트(`15 × STP` .. `15 × LDP; RET`) | `.init_array`에서 참조하는 Stage 1 부트스트랩 레지스터 보존 래퍼 |
| `0x23C`(572) | 확인된 Stage 1 외부 래퍼 크기(`outer_size`) |
| `0x1000` / `0x20` | Stage 1 파라미터 영역 크기 / 8-dword Stage 1 워드 헤더 크기 |
| `0xBF20165D`, `0xBF189BDD` | 확인된 빌드 계열별 Stage 1 워드 암호 상수 `C` |
| `lib__XXXX__.so`, `assets/<id>/data1.dat` | 동반 프로텍터 스텁 공유 라이브러리 및 라이브러리별 설정 블롭 |

## 암호, 컨테이너 및 Stage 2 스트림

| 상수 | 적용 범위 |
| --- | --- |
| `0x94511DD2` / `0x579357EB` | `gf32_mul_fixed`에서 사용하는 GF(2³²) 고정 승수 / 기약 다항식 |
| `00 01 0e 00` | `Module9bConfig` 키 스케줄 마커(플래그 `0x0100`, AES-256 14라운드, 라운드 키 `0xF0`바이트) |
| `0xE2` | 루트 Stage 2 인터프리터 스트림 ID |
| `0xE3`..`0xE8` / `0xF3`..`0xF8` | 중첩 인터프리터 모듈 및 각 모듈의 직접 입력 스트림 슬라이스(`sid = command_id - 0x10`) |
| `0xD0` | Stage 2 진입 시점에 등록되는 `SHT_LOUSER` 파일 후미 매핑 슬롯 |
| `0x1800` / `0x18` | Stage 2 런타임 모듈 테이블 전체 크기 / 슬롯 보폭(총 256슬롯) |
| `0x5C`(23 dword) | Stage 2 레코드 디스크립터 및 `0x9D` `ProtectedDescriptor` 바이트 크기 |
| `0x2` / `0x100` | 디스크립터 `DIRECT_FLAG`(원시 슬라이스) / `init` 및 `entry` 콜백 생략 플래그 |
| `0x1B00` | `ContainerHeader` 내 허프만 테이블 최대 바이트 크기(`tree_size`) |

## 정적 복원 및 IL2CPP 메타데이터

| 상수 | 적용 범위 |
| --- | --- |
| `0x9B`, `0x9D`, `0x9E` | 필수 기본 ELF 복원 모듈(설정, 주·보조 컨테이너, 숨겨진 심볼) |
| `0x96`, `0x98`, `0x0C` | 선택적 정적 복원 모듈(보조 심볼 시드, `.init_array` 생성자 복원 인터프리터, `v24.1` 메타데이터 시드 및 예외 테이블) |
| `0x403`, `0x101`, `0x401`, `0x402` | 보조 AArch64 재배치 타입인 `RELATIVE`, `ABS64`, `GLOB_DAT`(`relocation1`) 및 `JUMP_SLOT`(`relocation2`) |
| `0xD65F03C0`(`RET`) | `0x98` 생성자 복원 수행 시 제거되는 `.init_array` 더미 타깃 |
| `0xFAB11BAF`, 버전 `24`(`v24.1`), `29`, `31`, `39` | 확인된 외부 IL2CPP 메타데이터 매직 넘버 및 지원 레이아웃 |
| `0xA6FAE968` | 모듈 `0x0C`에서 확인된 기본 `MethodDef` 순열 시드 |
| `0x2701F30`, `[0x9732CA38, 0xBAC4374F]` | 내장 XOR 마스킹 슬림 v24 메타데이터 크기 및 마스킹 해제 후 바이트 스왑된 헤더 프로브 dword 쌍 |
