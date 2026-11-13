---
description: "디스크 레이아웃, KONN 헤더 식별, 빌드 계열 분류 및 외부 컴패니언 분할 구조"
icon: folder-tree
---

# 보호된 파일 구조

보호된 Windows 바이너리는 첫 `0x1000` 바이트에 로드 가능한 외부 PE 헤더를 유지하고, 오프셋 `0x1000`에 암호화된 파라미터 헤더를 배치하며, 그 뒤쪽(또는 같은 디렉터리의 `._` 컴패니언 파일)에 단계별 로더와 압축된 애플리케이션 섹션을 저장합니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-box-archive"></i></td><td><strong>컨테이너 및 암호화된 헤더</strong></td><td>고정 오프셋 <code>0x1000</code> 분할 구조, 8-dword <code>info</code> 헤더 KDF, 페이로드 복사 범위.</td><td><a href="container-layout.md">컨테이너 및 암호화된 헤더</a></td></tr><tr><td><i class="fa-fingerprint"></i></td><td><strong>포맷 식별 및 빌드 계열</strong></td><td>콘텐츠 기반 <code>KONN</code> 탐지, PE32 및 PE32+ CLR 분류, 레이아웃 계열.</td><td><a href="recognition.md">포맷 식별 및 빌드 계열</a></td></tr><tr><td><i class="fa-copy"></i></td><td><strong>섹션 데이터 및 컴패니언 파일</strong></td><td><code>0x1080</code>의 비트 반전 섹션 데이터 기준 오프셋과 외부 <code>._</code> 컴패니언 매칭 및 오버레이.</td><td><a href="companion-layout.md">섹션 데이터 및 컴패니언 파일</a></td></tr></tbody></table>
