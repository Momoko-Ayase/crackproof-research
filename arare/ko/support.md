---
description: "지원하는 PE 및 CLR 입력 매트릭스, 패킹 거부 조건, 구조적 한도 및 로딩 규칙."
icon: circle-check
---

# 지원 범위

Arare는 Windows 10 및 Windows 11을 대상으로 하며, 소스에서 직접 빌드한 x86/WOW64 및 x64 네이티브·관리형 프로그램을 Windows 11 빌드 26100에서 실행하여 동작을 검증했습니다(Windows 10 단독 테스트 패스는 별도로 수행하지 않음). 관리형 실행은 .NET Framework 4.8(x86/x64), CoreCLR 10.0.12(x64), Mono 6.13(x86)에서 검증되었습니다.

## 지원 입력 매트릭스

| 입력 유형 | 내장(embedded) 프로필 | 컴패니언(`._`) 프로필 |
| --- | --- | --- |
| 네이티브 x86 EXE 또는 DLL | `pe32` | `pe32` |
| 네이티브 x64 EXE 또는 DLL | `pe64-classic`, `pe64-modern` | `pe64-classic` (DLL은 0이 아닌 엔트리 필요), `pe64-modern` |
| 네이티브 x64 DLL (전용 레이아웃) | `legacy-dll` | 지원 안 함 |
| IL 전용 x86 또는 AnyCPU DLL | `pe32` | `pe32` |
| 식별 가능한 IL 전용 x86 또는 AnyCPU C# EXE | `pe32` | `pe32` |
| IL 전용 x64 DLL | `legacy-dll`, `pe64-classic`, `pe64-modern` | `pe64-classic`, `pe64-modern` |
| IL 전용 x64 EXE | `pe64-classic`, `pe64-modern` | `pe64-classic`, `pe64-modern` |
| `COR20` `ILONLY` 플래그가 해제된 순수 IL DLL | 해당 비트 수의 IL 전용 DLL과 동일 | 해당 비트 수의 IL 전용 DLL과 동일 |

네이티브 IL2CPP 바이너리(`GameAssembly.dll` 및 호스트 EXE)는 일반 네이티브 PE로 패킹되며, 단독 `global-metadata.dat` 난독화는 Arare의 지원 범위에 포함되지 않습니다.

## 패킹 거부 조건

`arare protect`는 다음 조건에 해당하는 입력을 거부합니다.

### 네이티브 및 공통 PE 제약 사항

* **엔트리가 0인 클래식 컴패니언 DLL:** `AddressOfEntryPoint`가 0인 `pe64-classic` 컴패니언 DLL (엔트리가 없는 DLL은 내장 저장 방식이나 `pe64-modern` 프로필을 사용하십시오).
* **컴패니언 TLS 영역 충돌:** TLS 엔트리 범위가 로더의 보존 대상 물리 데이터 영역과 겹치는 x64 컴패니언 입력.
* **페이지 암호화 정렬 및 권한 조건:** 페이지 암호화가 활성화된 상태에서 쓰기 및 실행이 모두 허용된(`RWX`) 섹션이 있거나, `SectionAlignment < 0x1000`이거나, 실행 섹션의 `VirtualAddress`가 `0x1000` 단위로 정렬되지 않은 경우.
* **바인딩 전용 임포트:** `OriginalFirstThunk == 0`이면서 이미지 내부에 hint/name RVA 또는 VA가 없는 네이티브 임포트 디스크립터.
* **PE32 EXE 임포트 정규화 충돌:** 정적 언패커의 임포트 테이블 복구를 위해 섹션 이름이나 권한 재작성이 필요한 네이티브 PE32 EXE.
* **XFG 코드 익스포트:** 코드 익스포트와 `IMAGE_GUARD_XFG_ENABLED`가 함께 사용된 네이티브 모듈.
* **이미지 및 헤더 크기 상한:** 추가되는 Arare 섹션을 포함한 전체 이미지 크기가 `1 GiB`를 초과하거나, 섹션 개수가 `96`개를 넘거나, 섹션 헤더 크기가 `0x1000`바이트(`pe64-*` / `legacy-dll`) 또는 `0x400`바이트(`pe32`)를 초과하는 경우.

### 관리형 어셈블리 제약 사항

* 실제 C++/CLI 혼합 모드(mixed-mode) 코드, 네이티브 CLR 엔트리 포인트 또는 vtable 픽스업, ReadyToRun/AOT 이미지, 비 IL 메서드 본문.
* 강력한 이름(strong-name) 서명 또는 지연 서명(delay-signed) 어셈블리, 다중 모듈 어셈블리, 링크/익스포트된 모듈 테이블, 내장 Portable PDB 또는 테이블 번호가 `45` 이상인 CLI 메타데이터 테이블(`/debug:embedded` 등).
* `ILONLY`가 해제된 x86 관리형 EXE, `32BITREQUIRED` 또는 `32BITPREFERRED`가 설정된 PE32+ 관리형 입력, RVA 페이지 `[0x1000, 0x2000)` 구간이 이미 점유된 임포트 없는 `pe64-modern` 어셈블리, 또는 임포트 디렉터리가 0이 아니지만 첫 번째 디스크립터가 비어 있는 `pe64-modern` 관리형 입력.
* 네이티브 익스포트 테이블, 네이티브 예외/언와인드 또는 TLS 디렉터리, 로드 구성(load-config) 테이블, 지연 로드 임포트, `VirtualSize > SizeOfRawData`인 섹션, Edit-and-Continue/포인터 메타데이터 테이블, CLI `vararg` 메서드, 예약된 `Arare.Managed` 네임스페이스 내부의 타입.
* 제네릭 패딩으로 추가되는 `TypeDef` 행이 `524,288`개를 초과하는 메타데이터 확장, 또는 중첩 깊이 `128`단계나 타입 요소 `65,536`개를 초과하는 시그니처 반환 타입.

## 레이아웃 및 런타임 로딩 참고 사항

* **실행 섹션 내부의 데이터 익스포트:** PE 익스포트 테이블은 엔트리가 코드인지 데이터인지 구분하지 않으므로, 실행 섹션 내부를 가리키는 비포워더(non-forwarder) 익스포트는 패킹 시 거부하지 않고 코드 익스포트 가드 썽크(guard thunk)로 감쌉니다. 익스포트할 데이터 심볼은 실행 권한이 없는 데이터 섹션에 배치하십시오.
* **바이트 배열 로드와 디스크 파일 로드:** 컴패니언 방식으로 패킹된 관리형 어셈블리는 디스크 파일 로드가 필요하며 `Assembly.Load(byte[])` 호출을 거부합니다. `ILONLY`가 해제된 순수 IL DLL은 표준 CLR 혼합 모드 로딩 규칙을 따릅니다(.NET Framework 및 CoreCLR에서는 비트 수가 일치하는 프로세스에서 디스크 파일로 로드해야 하며, Mono는 디스크와 바이트 배열 로드를 모두 지원함).
