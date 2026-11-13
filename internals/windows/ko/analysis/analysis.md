---
description: "실전 분석 워크플로, 설계상 한계점, -GMD IL2CPP 메타데이터 재매핑 및 상수 표."
icon: compass
---

# 분석 노트

CrackProof로 보호된 Windows 바이너리의 정적·동적 분석은 구조 교차 검증, 디버그 로그 코드와 각 스테이지 루틴의 대응, 형식별 사후 검증을 결합해 수행합니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-check"></i></td><td><strong>분석 워크플로</strong></td><td>디버그 로그 활성화, 스테이지 탐색, 페이지 보호 모듈 덤프 및 PE 출력 검증 절차.</td><td><a href="workflow.md">분석 워크플로</a></td></tr><tr><td><i class="fa-triangle-exclamation"></i></td><td><strong>확인된 한계점</strong></td><td>VM 탐지, 디버그 로그, 온디맨드 페이지 복호화, 드라이버 및 CRC 체인에서 재현되는 설계상 한계점.</td><td><a href="observed-limitations.md">확인된 한계점</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>il2cpp 메타데이터 난독화</strong></td><td>Unity IL2CPP 빌드의 키 없는 Windows <code>-GMD</code> 희소 MethodDef 토큰 재매핑 복원 방법.</td><td><a href="il2cpp-metadata.md">il2cpp 메타데이터 난독화</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>상수 및 오프셋</strong></td><td>매직 값, 컨테이너 수식, PE32/PE32+ 필드 오프셋 및 바이트코드 명령어 기준 표.</td><td><a href="constants.md">상수 및 오프셋</a></td></tr></tbody></table>
