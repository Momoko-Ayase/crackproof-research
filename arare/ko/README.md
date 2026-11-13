---
description: "관찰된 CrackProof 레이아웃을 재현하는 소스 빌드 Windows PE 프로텍터."
icon: shield-halved
---

# Arare

Arare는 소스 코드부터 직접 빌드하는 Windows PE 프로텍터입니다. 상용 도너(donor) 바이너리나 추출된 스텁 프로필을 사용하지 않고 자체 네이티브 및 관리형 로더를 컴파일하며, 빌드마다 고유 키, AES 키 스케줄, 바이트코드 프로그램, Huffman/LZ 압축 테이블, 단계 메타데이터를 새로 생성합니다.

네이티브 보호는 4가지 구조 계열(`pe32`, `pe64-classic`, `pe64-modern`, `legacy-dll`)에 걸쳐 x86 및 x64 EXE와 DLL을 지원합니다. 관리형 보호는 생성된 ECMA-335 시작 타입으로 IL 어셈블리를 감싸고 독립 네이티브 디코더로 검증합니다. 수정하지 않은 Senbei 1.3.1로 정적 복구 호환성을 검증하고, Windows 11 빌드 26100 환경에서 원본, 보호본, 언패킹본 프로그램을 직접 실행하여 동작을 확인합니다(대상 OS는 Windows 10 및 Windows 11).

내장 런타임은 빌드별 `%TEMP%` 폴더 게이트 방식의 디버그 로깅, 수동 매핑(manual mapping) 헬퍼 DLL 내부의 설정 가능한 환경 검사, 페이지 암호화 및 온디맨드 페이지 복호화(`KiUserExceptionDispatcher`), 시드 기반 로더 코드 변형, 시작 완료 후 메타데이터 소거를 구현합니다. 검사에 실패하면 활성 로그에 `AAA-BBB-CCC` 종료 코드를 기록하며, 네이티브 EXE는 기본적으로 종료 전에 `EXCEPTION_ACCESS_VIOLATION`을 발생시켜(`--antidebug-av=on`) 연결된 디버거가 즉시 중단되도록 합니다. 반면 DLL, `--antidebug-av=off`가 지정된 네이티브 EXE, 관리형 모듈은 곧바로 `TerminateProcess`를 호출합니다.

기반 포맷은 [CrackProof Windows 내부 구조](https://app.gitbook.com/s/FlY9nVrA6FxLQBrkLIc2/)를 참고하십시오. 정적 언패킹은 [Senbei](https://app.gitbook.com/s/mrjeUWp0ICb0dlYX4QBv/)에 문서화되어 있습니다.

## 섹션 구성

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-terminal"></i></td><td><strong>사용법</strong></td><td>CLI <code>protect</code>, <code>inspect</code>, <code>verify</code> 명령어, 프로필, 환경 검사, 페이지 암호화 및 디버그 로그.</td><td><a href="usage.md">사용법</a></td></tr><tr><td><i class="fa-window-maximize"></i></td><td><strong>GUI</strong></td><td>배치 작업 대기열, 행별 프로필 및 검사 재정의, PowerShell 스크립트 내보내기 및 검증을 위한 WPF 프런트엔드.</td><td><a href="gui.md">GUI</a></td></tr><tr><td><i class="fa-circle-check"></i></td><td><strong>지원 범위</strong></td><td>지원하는 네이티브 및 관리형 계열, 테스트된 CLR 호스트, 패킹 거부 조건 및 구조적 한도.</td><td><a href="support.md">지원 범위</a></td></tr><tr><td><i class="fa-diagram-project"></i></td><td><strong>설계</strong></td><td>크레이트 경계, 단일 저장 방식의 섹션 및 리소스 인코딩, 3단계 런타임 시작 흐름 및 상용 빌드와의 차이.</td><td><a href="design.md">설계</a></td></tr><tr><td><i class="fa-hammer"></i></td><td><strong>개발</strong></td><td>네이티브 로더 및 관리형 도구 빌드, Senbei 1.3.1 오라클 실행 및 워크스페이스 규칙.</td><td><a href="development.md">개발</a></td></tr></tbody></table>

## 범위 및 라이선스

Android 타깃, 단독 IL2CPP `global-metadata.dat` 난독화, `protect` 명령의 커널 드라이버 옵션은 지원 범위에 포함되지 않습니다(실험용 커널 프로바이더는 `kernel/` 아래에 별도로 분리되어 있음).

{% hint style="info" %}
**라이선스 분리.** 호스트 도구(`arare-cli`, `arare-engine`, `tools/managed`, `gui`, `verification/senbei-oracle`)는 `AGPL-3.0-only` 라이선스를 따릅니다. PE 파서(`arare-pe`), 코덱(`arare-codec`), 내장되는 모든 네이티브 및 관리형 런타임 코드(`arare-runtime`, `runtime/`)는 `MIT` 라이선스이므로 보호된 바이너리에는 AGPL 코드가 포함되지 않습니다.
{% endhint %}
