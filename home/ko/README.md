---
description: "CrackProof 보호 포맷과 런타임 동작을 분석한 독립 기술 연구 문서입니다."
icon: house
layout:
  width: wide
  title:
    visible: true
  description:
    visible: true
  tableOfContents:
    visible: false
  outline:
    visible: false
  pagination:
    visible: false
  metadata:
    visible: false
  tags:
    visible: true
  actions:
    visible: false
---

# CrackProof 연구

CrackProof®는 HyperTech에서 개발한 상용 바이너리 보호 시스템 제품군입니다. 이 사이트는 독자적인 분석으로 검증한 파일 포맷, 데이터 변환, 단계별 로더 및 런타임 구성 요소를 문서화합니다.

분석 대상은 Windows PE 파일(CrackProof for Windows®)과 Android AArch64 공유 라이브러리입니다. 플랫폼마다 컨테이너 포맷과 복원 파이프라인이 다르므로 내부 구조를 별도 섹션으로 나누어 설명합니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-desktop"></i></td><td><strong>Windows 내부 구조</strong></td><td>CrackProof for Windows®의 보호된 PE 레이아웃, 암호 알고리즘, 단계별 로딩, PE 재구성 및 런타임 검사.</td><td><a href="https://app.gitbook.com/s/FlY9nVrA6FxLQBrkLIc2/">CrackProof for Windows® 내부 구조</a></td></tr><tr><td><i class="fa-mobile-screen-button"></i></td><td><strong>Android SO 내부 구조</strong></td><td>보호된 AArch64 ELF 레이아웃, 중첩 모듈 스트림, 컨테이너 디코딩, ELF 복원 및 IL2CPP 메타데이터.</td><td><a href="https://app.gitbook.com/s/lHw4BUMHINzsXego7Ota/">CrackProof Android SO 내부 구조</a></td></tr><tr><td><i class="fa-code"></i></td><td><strong>검증 및 레퍼런스</strong></td><td>Windows 변환 로직의 실행 가능한 테스트 벡터, Python 레퍼런스 구현 및 익명화된 디버그 로그.</td><td><a href="https://app.gitbook.com/s/B5aYhrgw97Xp8Yd3YI4L/">검증 및 레퍼런스</a></td></tr><tr><td><i class="fa-screwdriver-wrench"></i></td><td><strong>Senbei</strong></td><td>보호된 Windows PE 파일, Android 공유 라이브러리 및 IL2CPP 메타데이터용 정적 언패커: CLI, 데스크톱 GUI, 설계 및 개발 가이드.</td><td><a href="https://app.gitbook.com/s/mrjeUWp0ICb0dlYX4QBv/">Senbei</a></td></tr><tr><td><i class="fa-shield-halved"></i></td><td><strong>Arare</strong></td><td>관찰된 레이아웃 계열을 재현하는 소스 빌드 방식 Windows PE 프로텍터: CLI, GUI, 지원 범위, 설계 및 개발 가이드.</td><td><a href="https://app.gitbook.com/s/0DlVRRR5tmVrwFqVBmXG/">Arare</a></td></tr></tbody></table>

## 연구 범위

문서화된 모든 규칙은 바이너리 구조와 런타임 동작에서 직접 관찰한 결과에 기반합니다. 필드와 구성 요소 이름은 바이너리 내부 문자열, 디버그 로그 출력, 표준 플랫폼 명세를 따르며, 고유 명칭이 없는 항목은 실제 바이트 단위 동작에 따라 기술합니다. 여러 샘플에서 공통으로 확인되거나 내부 무결성 검사로 강제되는 동작만 포맷 규칙으로 일반화했습니다.

보호 대상 제품명, 배포 환경별 드라이버 파일명, 샘플을 식별할 수 있는 경로는 연구 섹션 전반에서 제외했습니다. Senbei와 Arare는 각각의 전용 제품 섹션에서 별도로 다룹니다.

{% hint style="warning" %}
**법적 고지.** 이 자료는 본인이 소유하거나 분석 권한을 명시적으로 부여받은 바이너리에 한해서만 사용하십시오. 기술적 보호 조치 우회에 관한 법률 및 라이선스 계약 조건은 관할권에 따라 다릅니다. 독자적으로 작성된 이 문서는 벤더의 소스 코드나 키를 포함하지 않으며, HyperTech와 무관하고, 복원된 바이너리의 재배포를 허가하지 않습니다.
{% endhint %}
