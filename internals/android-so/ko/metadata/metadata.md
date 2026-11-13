---
description: "Android IL2CPP 메타데이터 메서드 토큰·methodIndex 순열 및 저장 방식"
icon: database
---

# 메타데이터

Unity IL2CPP 기반 Android 빌드에서 CrackProof는 `libil2cpp.so`와 함께 `global-metadata.dat`도 보호합니다. 메타데이터 버전과 패키징 방식에 따라 외부 `global-metadata.dat` 파일 내부의 메서드 토큰 또는 `methodIndex` 필드를 순열로 뒤섞거나(런타임에는 모듈 `0x0C`가 `mmap`을 후킹해 복원), 슬림 버전 24 메타데이터 블롭을 32비트 XOR 키로 마스킹하여 `.so` 데이터 섹션 내부에 내장합니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-hashtag"></i></td><td><strong>메서드 토큰</strong></td><td>버전 29, 31, 39의 5라운드 역순열, 버전 31의 테이블 순서 기반 <code>-GMD</code> 폴백, 그리고 버전 24.1 <code>methodIndex</code> 복원.</td><td><a href="method-tokens.md">메서드 토큰</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>저장 레이아웃</strong></td><td>외부 <code>global-metadata.dat</code> 페어링 규칙과 내장 XOR 마스킹 슬림 v24 메타데이터 블롭 비교.</td><td><a href="storage-layouts.md">저장 레이아웃</a></td></tr></tbody></table>
