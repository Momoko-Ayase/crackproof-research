---
description: "PE 섹션 헤더, 엔트리 포인트, 데이터 디렉터리, 임포트, TLS, 재배치 및 CLR 복원"
icon: puzzle-piece
---

# PE 재구성

섹션 복구가 끝나면 RVA 기준으로 배치된 메모리 버퍼(`SizeOfImage`바이트)가 만들어집니다. 이 버퍼를 실제로 로드 가능한 정상 PE 파일로 되돌리려면, 빌드 레이아웃 계열에 맞춰 삭제되거나 다른 위치로 바뀐 헤더 필드, 임포트 테이블, TLS 상태, 익스포트 테이블, 기준 재배치, `.text` 페이지 스크램블, CLR 메타데이터를 모두 복원해야 합니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-memory"></i></td><td><strong>헤더, 섹션 및 0 채우기 범위</strong></td><td>RVA 매핑 섹션 헤더, 32비트 파일 밀착 배치, EP/디렉터리 일시 복호화 블록, <code>.bss</code> 0 채우기 체인을 다룹니다.</td><td><a href="memory-image.md">헤더, 섹션 및 0 채우기 범위</a></td></tr><tr><td><i class="fa-sitemap"></i></td><td><strong>임포트, TLS 및 익스포트</strong></td><td>계열별 임포트 복구, <code>.kmiat</code> 재구축, TLS 복원 및 재배치 재활성화, 스텁 익스포트 복원을 다룹니다.</td><td><a href="imports-tls-exports.md">임포트, TLS 및 익스포트</a></td></tr><tr><td><i class="fa-cubes"></i></td><td><strong>기준 재배치, 페이지 변환 및 CLR 데이터</strong></td><td><code>/FIXED</code> 대 ASLR 재배치 정책, <code>.text</code> 스크램블 실행 순서, 정밀 CLR 메타데이터 복원을 다룹니다.</td><td><a href="relocations-managed.md">기준 재배치, 페이지 변환 및 CLR 데이터</a></td></tr></tbody></table>
