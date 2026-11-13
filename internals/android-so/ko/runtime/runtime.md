---
description: "Stage 1 스텁부터 중첩 Stage 2 인터프리터와 환경 검사까지의 로드 시점 실행"
icon: play
---

# 런타임

로드 시점에 Android 동적 링커가 비워진 ELF 이미지를 매핑하고 `.init_array`를 실행하면 제어가 Stage 1 부트스트랩 스텁으로 넘어갑니다. Stage 1은 Stage 2(`0xE2`)를 매핑해 복호화하고, Stage 2는 256슬롯 모듈 테이블을 할당한 뒤 중첩 인터프리터 스트림(`0xE2`..`0xE8`)을 순회하며 유저모드 환경 및 무결성 검사를 수행합니다. 이후 메모리 상에서 ELF 세그먼트와 재배치를 복원하고 모듈 `0x98`을 통해 원본 생성자를 호출합니다.

정적 복원에는 컨테이너, 심볼, 재배치, 생성자, 메타데이터 관련 아티팩트(`0x9B`, `0x9D`, `0x9E` 및 선택적 모듈인 `0x96`, `0x98`, `0x0C`)만 필요하며, 환경 검사 모듈은 런타임에만 실행됩니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-bolt"></i></td><td><strong>Stage 1 부트스트랩</strong></td><td><code>/proc/self/maps</code> 기반 자체 경로 탐색, <code>SHT_LOUSER</code> 복호화, 페이지 크기 판별 및 레지스터 제어 전달.</td><td><a href="stage1-bootstrap.md">Stage 1 부트스트랩</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>Stage 2 인터프리터</strong></td><td>256슬롯 모듈 테이블, <code>0x5C</code> 레코드 디스크립터 및 다단 <code>0xE2</code>..<code>0xE8</code> 스트림 실행.</td><td><a href="stage2-interpreter.md">Stage 2 인터프리터</a></td></tr><tr><td><i class="fa-user-shield"></i></td><td><strong>환경 및 무결성 검사</strong></td><td><code>NativeBridge</code> 탐지, <code>PTRACE_SEIZE</code> 보조 프로세스, <code>/proc/&lt;pid&gt;/mem</code> 감시 및 APK 서명 검증.</td><td><a href="environment-checks.md">환경 및 무결성 검사</a></td></tr><tr><td><i class="fa-layer-group"></i></td><td><strong>런타임 모듈</strong></td><td>인터프리터, 복원, 환경 검사 전반에서 확인된 Stage 2 모듈 식별자 카탈로그.</td><td><a href="modules.md">런타임 모듈</a></td></tr></tbody></table>
