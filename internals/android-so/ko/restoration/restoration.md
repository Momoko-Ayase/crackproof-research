---
description: "Stage 2 모듈 추출, 동적 링킹 테이블 복구 및 정상 ELF64 공유 라이브러리 재구성"
icon: puzzle-piece
---

# 복원

정적 복원은 두 단계로 진행됩니다. 먼저 `SHT_LOUSER` 섹션에서 Stage 2 모듈 세트를 추출한 뒤, ELF 로드 세그먼트, 동적 심볼 테이블 및 재배치 테이블, 섹션 헤더 테이블을 재구성하고 출력 이미지를 검증합니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-route"></i></td><td><strong>모듈 스트림</strong></td><td>필수 기본 모듈(<code>0x9B</code>, <code>0x9D</code>, <code>0x9E</code>)과 선택적 정적 복원 모듈(<code>0x96</code>, <code>0x98</code>, <code>0x0C</code>)을 정리합니다.</td><td><a href="module-streams.md">모듈 스트림</a></td></tr><tr><td><i class="fa-link"></i></td><td><strong>동적 링킹</strong></td><td>숨김 심볼, <code>0x96</code> 심볼 역순열, 생략된 <code>libc</code> PLT 슬롯, 생성자 복구, <code>PT_LOAD</code> 배치를 다룹니다.</td><td><a href="dynamic-linking.md">동적 링킹</a></td></tr><tr><td><i class="fa-file-export"></i></td><td><strong>ELF 출력</strong></td><td><code>SHT_LOUSER</code> 제거, <code>e_entry</code> 초기화, 비할당 섹션 오프셋 조정, 필수 검증과 진단 검사를 다룹니다.</td><td><a href="elf-output.md">ELF 출력</a></td></tr></tbody></table>
