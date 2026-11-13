---
description: "실패 시 즉시 중단하는 구조 검증 체크리스트와 확인된 Android SO 형식 상수."
icon: compass
---

# 분석

ELF 식별, Stage 1·Stage 2 복호화, 동적 테이블 재구축 및 IL2CPP 메타데이터 복원 과정에서는 다음 단계로 넘어가기 전에 각 단계의 구조적 경계 조건을 검증합니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-check"></i></td><td><strong>검증 체크리스트</strong></td><td>식별, 스트림 추출, ELF 재구성 및 메타데이터 전반의 순차적 구조 검증 항목.</td><td><a href="validation.md">검증 체크리스트</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>상수</strong></td><td>확인된 매직 값, 오프셋, 암호 상수 및 모듈 ID 요약 표.</td><td><a href="constants.md">상수</a></td></tr></tbody></table>
