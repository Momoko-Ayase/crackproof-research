---
description: "자가 복호화 로더 스테이지 체인과 레이아웃 변종별 Windows 섹션 복구 과정"
icon: stairs
---

# 로딩 및 섹션 복구

보호된 Windows 컨테이너는 5~8단계의 자가 복호화 로더 스테이지를 순차적으로 복호화합니다. 각 단계는 이전 스테이지의 CRC-32 체크섬, 삼각수 키 진행, 빌드별 바이트코드 스텁을 거쳐 풀리며, 마지막 스테이지에서 최종 섹션 복구 테이블이 드러납니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-link"></i></td><td><strong>스테이지 체인과 마커 레이아웃</strong></td><td>복합 스테이지 복호화 구조와 9단계로 구성된 64비트 마커 레이아웃 복구 파이프라인을 다룹니다.</td><td><a href="stage-chain.md">스테이지 체인과 마커 레이아웃</a></td></tr><tr><td><i class="fa-code-branch"></i></td><td><strong>PE32, DLL 및 마커리스 레이아웃</strong></td><td>표준 및 컴팩트 PE32 셸, 전용 64비트 DLL 고정 테이블, 마커리스 64비트 탐색 방식을 비교합니다.</td><td><a href="layout-variants.md">PE32, DLL 및 마커리스 레이아웃</a></td></tr><tr><td><i class="fa-magnifying-glass"></i></td><td><strong>구조적 탐색 및 검증</strong></td><td>시험 복호화, 압축 블록 검증, <code>.text</code> 페이지 스크램블 선택 규칙을 설명합니다.</td><td><a href="discovery-validation.md">구조적 탐색 및 검증</a></td></tr></tbody></table>
