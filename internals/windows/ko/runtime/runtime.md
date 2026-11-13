---
description: "부팅 시퀀스, 상태 코드, 안티분석 검사, 온디맨드 페이지 복호화 및 Htsysm 드라이버."
icon: play
---

# 런타임 동작

보호된 Windows 바이너리는 실행 시 원본 엔트리 포인트(`280` 단계)로 점프하기 전에 CrackProof 부트스트랩 로더를 먼저 실행합니다. 로더는 조건부 디버그 로그를 열고 보조 DLL을 메모리에 수동 매핑한 뒤, OS, VM, 디버거 및 프로세스 환경을 검사합니다. 이어서 설정에 따라 `Htsysm` 커널 드라이버를 초기화하고 섹션과 임포트를 복원하며, 실행 페이지를 다시 암호화해 `KiUserExceptionDispatcher` 후킹 기반의 온디맨드 페이지 복호화를 적용합니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-ol"></i></td><td><strong>시작 시퀀스와 상태 보고</strong></td><td>12비트 부팅 상태 코드, <code>%temp%</code> 12자리 16진수 로그 조건, <code>ErrLog-Pec</code> 메일슬롯 및 <code>AAA-BBB-CCC</code> 오류 코드.</td><td><a href="startup-status.md">시작 시퀀스와 상태 보고</a></td></tr><tr><td><i class="fa-user-shield"></i></td><td><strong>환경 및 안티분석 검사</strong></td><td>디버거, VM, 부팅 옵션, 인젝션된 DLL 및 스레드, <code>A11</code>/<code>A15</code> 호스트 검증 및 시스템 DLL 언후킹 검사.</td><td><a href="environment-checks.md">환경 및 안티분석 검사</a></td></tr><tr><td><i class="fa-lock"></i></td><td><strong>페이지 보호 및 로더 코드</strong></td><td><code>KiUserExceptionDispatcher</code> 온디맨드 페이지 복호화, scribble, 다형성 코드, 디코이 및 디스크 자체 매핑.</td><td><a href="page-protection.md">페이지 보호 및 로더 코드</a></td></tr><tr><td><i class="fa-layer-group"></i></td><td><strong>수동 매핑 보조 모듈</strong></td><td>내장 보조 모듈(<code>it</code>, <code>dt</code>, <code>cm</code>, <code>dm</code>, <code>sk</code>, <code>pm</code>)의 역할과 PEB 모듈 목록에서 제외되는 구조.</td><td><a href="mapped-modules.md">수동 매핑 보조 모듈</a></td></tr><tr><td><i class="fa-gears"></i></td><td><strong>Htsysm 커널 구성 요소</strong></td><td>1세대부터 3세대까지의 커널 드라이버(<code>Htsysm</code>, <code>Htsysm7679</code>, <code>Htsysm1B4001</code> 등 <code>0xAA02</code> <code>ObRegisterCallbacks</code> 드라이버).</td><td><a href="kernel-components.md">Htsysm 커널 구성 요소</a></td></tr></tbody></table>
