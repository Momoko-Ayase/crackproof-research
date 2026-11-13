---
description: "보호된 Android ELF64 라이브러리 식별과 Stage 1 및 2 페이로드 경계"
icon: folder-tree
---

# 파일 포맷

보호된 Android 공유 라이브러리는 유효한 리틀 엔디안 ELF64 AArch64 바이너리 형태를 그대로 유지합니다. 동적 링킹 관련 섹션은 섹션 헤더 테이블에 남아 있지만, 로드 가능한 코드와 데이터 영역은 비워지고 실제 페이로드는 파일 끝의 단일 `SHT_LOUSER` 섹션으로 옮겨집니다.

헤더 타입, 섹션 오프셋, 파라미터 경계, 중첩 스트림 범위가 모두 검증 조건을 통과해야 유효한 보호 파일로 식별됩니다. 로드 시점에 동일한 구조를 탐색하는 과정은 [Stage 1 부트스트랩](../runtime/stage1-bootstrap.md)에서 다룹니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-file-code"></i></td><td><strong>보호된 ELF</strong></td><td>필수 ELF64 헤더, 동적 섹션, <code>.init_array</code> 부트스트랩 슬롯, 보조 APK 아티팩트를 설명합니다.</td><td><a href="protected-elf.md">보호된 ELF</a></td></tr><tr><td><i class="fa-box-archive"></i></td><td><strong>Stage 1 헤더</strong></td><td><code>SHT_LOUSER</code> 페이로드 섹션 레이아웃, 32바이트 파라미터 헤더, 상대 오프셋 경계를 설명합니다.</td><td><a href="stage1.md">Stage 1 헤더</a></td></tr><tr><td><i class="fa-bars-staggered"></i></td><td><strong>Stage 2 스트림</strong></td><td><code>0x5C</code>바이트 레코드 디스크립터, 직접 슬라이스와 하위 스트림 분기, 컨테이너 페이로드 디스패치를 설명합니다.</td><td><a href="stage2-streams.md">Stage 2 스트림</a></td></tr></tbody></table>
