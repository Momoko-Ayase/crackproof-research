---
description: "보호된 Android ELF64 공유 라이브러리와 IL2CPP 메타데이터의 단계별 검증"
icon: list-check
---

# 검증 체크리스트

분석 및 복원 대상인 모든 Android `.so`와 `global-metadata.dat` 파일은 아래의 구조적 검사를 순서대로 통과해야 합니다. 필수 불변 조건을 하나라도 만족하지 못하면 불완전한 출력 파일을 남기지 않고 복원을 즉시 중단합니다.

{% stepper %}
{% step %}
## ELF 식별 및 `SHT_LOUSER` 경계 검증

* ELF64, 리틀 엔디언, `EM_AARCH64`(`183`), `e_phentsize == 0x38`, `e_shentsize == 0x40` 여부와 유효한 UTF-8 `.shstrtab`을 확인합니다.
* `.dynsym`, `.dynstr`, `.gnu.version`, `.gnu.version_r`과 하나 이상의 심볼 해시 섹션(`.gnu.hash` 또는 `.hash`, 혹은 둘 다)이 존재해야 합니다. 복원 단계에서는 `.dynamic`, `.rela.dyn`, `.rela.plt`도 각각 정확히 하나씩 필요합니다.
* 섹션 헤더 테이블의 마지막 엔트리로 전용 섹션 `SHT_LOUSER`(`0x80000000`)가 정확히 하나 존재해야 하며, 파일 기반 `PT_LOAD` 범위 끝의 16바이트 정렬 지점에서 시작해야 합니다(사이 간격은 모두 0 패딩이어야 함).
{% endstep %}

{% step %}
## Stage 1 및 Stage 2 스트림 추출

* `section_offset + outer_size` 위치에서 32바이트 Stage 1 워드 헤더를 디코딩하고, `reserved == 0`, `size_copy == payload_size`, `payload_size > 0 && payload_size % 4 == 0`, `payload_offset >= 0x20`, `payload_offset + payload_size <= section_size - outer_size`, `entry_offset < payload_size`, `protect_size <= payload_size` 조건을 검증합니다.
* 0이 아닌 가장 작은 페이로드 오프셋 이전 영역에서 Stage 2의 `0x5C` 레코드 테이블(`dw0`개, 최대 256개)을 파싱하며, 모든 슬라이스에서 `id_copy == command_id`와 상위 스트림 경계를 확인합니다.
* 모든 Huffman/LZ 압축 블록에서 압축 비트 소모량(`div_ceil(consumed_bits, 8) == src_len`), 출력 크기(`output_pos == out_len`), `pending == 0`이 정확히 일치해야 합니다.
* 필수 기본 모듈 `0x9B`, `0x9D`, `0x9E`가 모두 존재해야 합니다(`0x96`, `0x98`, `0x0C`는 존재하는 경우 함께 사용). 같은 모듈 ID가 여러 번 등장할 때 SHA-256 다이제스트가 동일하면 하나로 합치고, 다이제스트가 서로 다르면 오류로 처리합니다.
{% endstep %}

{% step %}
## 동적 테이블 재구축 및 ELF 출력

* `0x9E`의 숨겨진 심볼 인덱스(`0 < target_index < symbol_count`, 중복 없음)와 `.dynstr` 경계를 검증하고, 프로텍터 후미 심볼(`dlerror`, `__stack_chk_guard`, `__stack_chk_fail`)을 제거합니다. 이어서 `0x96`이 있으면 보조 심볼 인덱스의 순열을 되돌리고, 제외된 `libc` PLT 슬롯을 판별하며, 정의된 심볼 재배치를 정렬된 `R_AARCH64_RELATIVE` 앞부분 구간(`DT_RELACOUNT`)으로 정규화하고, `0x98`이 있으면 생성자 복원을 적용합니다.
* 재구축된 테이블을 `.dynsym` 이후의 기존 영역 또는 새로 추가한 `PF_R` `PT_LOAD` 세그먼트에 배치하고, `SHT_LOUSER`를 제거하며 `e_entry`를 `0`으로 초기화한 뒤, 비할당(non-`SHF_ALLOC`) 섹션을 로드 가능 세그먼트 뒤로 재배치하여 원자적 교체 방식으로 저장하고 디스크에서 다시 파싱합니다.
* 저장 후 필수 검사(파싱 유효성, `PT_LOAD` 파일 범위, `.shstrtab`, `SHT_LOUSER` 제거 여부, `e_entry == 0`, `.dynsym` / `.rela.dyn` / `.rela.plt` 엔트리 개수 일치)를 수행하고 테이블 간 교차 링커 진단을 수행해 경고를 보고합니다.
{% endstep %}

{% step %}
## IL2CPP 메타데이터 검증

* `0xFAB11BAF` 매직과 버전 `24`(동일 애플리케이션의 모듈 `0x0C`와 짝지은 `v24.1`), `29`, `31`(시드 기반 5라운드 역순열 및 테이블 순서 기반 `-GMD` 폴백), 또는 `39`(압축 12바이트 섹션 디렉터리)의 검증된 테이블 레이아웃과 일치해야 합니다.
* 이미 정규 상태인 메타데이터는 변경하지 않고 그대로 유지하며(멱등성 보장), 복원 후에는 모든 메서드가 연속된 테이블 구간으로 단일 `Il2CppImage`에 속하는지와 정규 `0x06000000 | rid` 또는 `0..active_count` 범위를 만족하는지 검증합니다.
{% endstep %}
{% endstepper %}
