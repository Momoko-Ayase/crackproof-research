---
description: "CrackProof로 보호된 PE, Android SO, 메타데이터 정적 언패커."
icon: screwdriver-wrench
---

# Senbei

Senbei `1.4.0`은 CrackProof로 보호된 바이너리를 위한 정적 언패커이자 구조 검사 도구입니다. 대상 바이너리를 실행하거나 프로세스에 어태치하지 않고 개별 파일, Android 앱 패키지, 디렉터리에서 바이너리를 복원하고 검증합니다.

Windows 및 Linux용 네이티브 릴리스에는 명령줄 도구인 `senbei`와 데스크톱 워크벤치인 `senbei-gui`가 함께 포함되며, 영어, 중국어 간체, 중국어 번체, 일본어, 한국어 인터페이스를 지원합니다. 동일한 코어 엔진을 컴파일한 WebAssembly 빌드는 브라우저 로컬 환경에서 개별 Windows PE 파일과 메타데이터 파일을 처리합니다.

## 지원 입력

* **Windows PE (`PE32` 및 `PE32+`):** 보호된 `.exe` 및 `.dll` 모듈(네이티브 바이너리 및 관리형 .NET 어셈블리)과 외부 `.exe._`, `.dll._` 컴패니언 페이로드를 지원합니다.
* **Android 네이티브 라이브러리 (`ELF64` AArch64):** 보호된 단독 `.so` 파일과 `.apk`, `.apks`, `.xapk` 앱 패키지를 지원합니다.
* **Unity IL2CPP 메타데이터:** Windows `-GMD` (`v31`) 레이아웃과 Android 시드 기반(`v24.1`, `v29`, `v31`, `v39`) 또는 내장 XOR(`v24`) 레이아웃의 `global-metadata.dat` 파일을 지원합니다.

기반 컨테이너 포맷과 변환 구조는 [CrackProof Windows 내부 구조](https://app.gitbook.com/s/FlY9nVrA6FxLQBrkLIc2/) 및 [CrackProof Android SO 내부 구조](https://app.gitbook.com/s/lHw4BUMHINzsXego7Ota/)에 문서화되어 있습니다.

## 섹션 구성

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-terminal"></i></td><td><strong>사용법</strong></td><td>CLI 명령어(<code>unpack</code>, <code>inspect</code>, <code>--dry-run</code>, <code>--json</code>), 폴더 및 패키지 처리 규칙, 표시 언어, 플래그, 종료 코드.</td><td><a href="usage.md">사용법</a></td></tr><tr><td><i class="fa-window-maximize"></i></td><td><strong>GUI</strong></td><td>네이티브 데스크톱 워크벤치(<code>senbei-gui</code>): 배치 작업 큐, 상세 분석 뷰어, Hex + RVA 뷰어, PE 비교 및 설정.</td><td><a href="gui.md">GUI</a></td></tr><tr><td><i class="fa-diagram-project"></i></td><td><strong>설계</strong></td><td>9개 크레이트 워크스페이스 구성, 프로필 및 트레이스 아키텍처, Windows 및 Android 파이프라인, WebAssembly 경계.</td><td><a href="design.md">설계</a></td></tr><tr><td><i class="fa-hammer"></i></td><td><strong>개발</strong></td><td>CLI, 데스크톱 GUI 및 WebAssembly 타깃 빌드, 코퍼스/퍼징/동치성 테스트, 벤치마크 및 환경 변수.</td><td><a href="development.md">개발</a></td></tr></tbody></table>

## 인터페이스 요약

| 인터페이스 | 지원 대상 | 출력 및 리포트 |
| --- | --- | --- |
| `senbei` (CLI) | 개별 파일, 폴더, `.apk`/`.apks`/`.xapk` | 복원된 파일, 실행 로그, 컬러 터미널 출력, `--json` 스키마 v1 리포트 |
| `senbei-gui` (데스크톱) | 개별 파일, 폴더, `.apk`/`.apks`/`.xapk` | 복원된 파일, 대화형 **개요**/**상세 분석**/**Hex**/**비교**/**항목**/**로그** 탭, JSON 및 텍스트 리포트 내보내기 |
| 브라우저 (`web/`) | 개별 Windows PE 파일(`._` 컴패니언 포함) 및 `global-metadata.dat` | 브라우저 내 로컬 다운로드 및 `Export JSON` 리포트 (입력 데이터가 기기 외부로 전송되지 않음) |
