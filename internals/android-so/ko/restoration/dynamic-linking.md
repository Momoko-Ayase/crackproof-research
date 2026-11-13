---
description: "동적 심볼, 문자열, 해시, 재배치, PLT 슬롯, 생성자 복원 및 PT_LOAD 배치"
icon: link
---

# 동적 링킹

`0x9D`의 주 컨테이너 데이터로 ELF 이미지의 비워진 `PT_LOAD` 영역을 채운 뒤에는, CrackProof가 제거했거나 `0x9D`, `0x9E`, `0x96`, `0x98`에 분산해 둔 동적 링킹 테이블을 재구성합니다.

{% stepper %}
{% step %}
## 숨겨진 심볼 복원 및 프로텍터 후미 임포트 제거

모듈 `0x9E`는 `{u32 blob_size, u32 secondary_record_count}`로 시작하며, `+0x08` 오프셋부터 `{u32 count, u32 symbol_offset, u32 index_offset, u32 string_offset}` 헤더와 24바이트 `Elf64_Sym` 엔트리 `count`개, 대상 `.dynsym` 인덱스(`u32`) `count`개, NUL 종료 심볼 이름(0~3바이트 제로 패딩 포함)이 차례로 이어집니다. 각 패치는 고유한 인덱스(`0 < target_index < symbol_count`)를 가리켜야 하며, `st_name` 위치의 심볼 이름은 `.dynstr` 범위 안에 들어가야 합니다(0으로 채워진 공간에 기록하거나 동일한 기존 문자열과 일치해야 함).

`0x9E`의 최대 `target_index` 뒤에 남는 후미 심볼이 프로텍터가 주입한 `{"dlerror", "__stack_chk_guard", "__stack_chk_fail"}` 임포트로만 구성된 경우, 보조 심볼을 추가하기 전에 해당 후미 심볼과 이를 참조하는 모든 재배치 항목을 제거합니다.
{% endstep %}

{% step %}
## 보조 심볼 추가 및 재배치 인덱스 순열 해제

`0x9D`의 보조 ELF 컨테이너는 `relocation1`(`.rela.dyn` 후보), `relocation2`(`.rela.plt` 후보), 보조 동적 심볼 테이블 `.dynsym`(인덱스 `0`의 널 엔트리와 `N - 1`개의 외부 심볼), 보조 `.dynstr`을 제공합니다. 널이 아닌 심볼을 주 `.dynsym` 뒤에 추가하고, 이에 맞춰 `.dynstr`을 확장한 뒤 `.gnu.version`에는 `VER_NDX_GLOBAL = 1`을 기록합니다(`.gnu.version_r`은 복원된 주 이미지의 데이터를 그대로 유지합니다).

모듈 `0x96`이 존재하는 경우(`N > 1`), `relocation1`과 `relocation2` 내 0이 아닌 보조 심볼 인덱스(`1..N-1`)는 `0x96`에서 추출한 32비트 `auxiliary_symbol_seed`를 사용해 재배치 행(`row`)마다 순환 이동되어 있습니다.

```text
s2       = (seed * seed) & 0xFFFFFFFF
left     = ((s2 >> (row & 0x1B)) + 0x1BC5) & 0xFFFFFFFF
right    = (((s2 << (row & 3)) & 0xFFFFFFFF) + 0x2048) & 0xFFFFFFFF
rotation = (left | right) % (N - 1)
```

각 행에 적용된 순환 이동을 `N - 1` 모듈러 연산으로 되돌린 뒤 `old_symbol_count - 1`을 더하면, 각 `r_info`가 병합된 `.dynsym` 슬롯을 참조하게 됩니다.
{% endstep %}

{% step %}
## 제외된 5개 `libc` PLT 슬롯 복원

CrackProof는 `relocation2`에서 최대 5개의 표준 `libc` 문자열·메모리 함수(`strlen`, `strcmp`, `memset`, `strcpy`, `strchr`)를 제외하여, `.got.plt`의 `0x18`바이트 헤더 뒤에 참조되지 않는 빈 슬롯을 남깁니다. 복원 과정에서는 각 빈 슬롯을 `.plt + 0x20 + slot * 0x10`(및 `ADRP X16/X17; ADD; BR` 형태의 컴파일러 베니어(veneer))에 대응시킨 뒤, `.text` 전반의 AArch64 호출 지점에서 인자 레지스터와 반환값 사용 패턴을 분석하여 일치하는 함수에 대해 `SHN_UNDEF` `STT_FUNC` 심볼을 추가하고 빠진 `R_AARCH64_JUMP_SLOT`(`0x402`) 레코드를 `.rela.plt`에 생성합니다.
{% endstep %}

{% step %}
## `.rela.dyn` 정규화, 심볼 해시 재구축 및 생성자 복원

대상 심볼이 정의되어 있는(`st_shndx != SHN_UNDEF`) `.rela.dyn` 레코드(`R_AARCH64_ABS64 = 0x101` 또는 `R_AARCH64_GLOB_DAT = 0x401`)는 `r_addend = st_value + r_addend`를 갖는 `R_AARCH64_RELATIVE`(`0x403`) 항목으로 변환합니다. 모든 `R_AARCH64_RELATIVE` 엔트리는 `r_offset` 기준으로 정렬하여 `.rela.dyn` 앞부분에 배치하고, 해당 앞부분 개수로 `DT_RELACOUNT`를 갱신합니다.

입력 ELF에 포함된 심볼 해시 섹션(`.gnu.hash`, SysV `.hash`, 또는 둘 다)은 최종 `.dynsym`을 기준으로 재구축합니다. 모듈 `0x98`이 존재하면 제한된 AArch64 인터프리터로 `entry_offset`부터 실행해(`X0 = runtime`, `[X0 + 8] = image_base`, `RET` 시점에 `W0 == 1` 확인) 숨겨진 생성자 포인터를 복원합니다. 이어서 `.init_array`의 Stage 1 부트스트랩 슬롯을 교체하고, `RET` 명령어(`0xD65F03C0`)만 있는 더미 항목을 제거한 뒤 `.init_array`/`.fini_array` 섹션 크기와 `DT_INIT_ARRAYSZ`/`DT_FINI_ARRAYSZ`를 갱신합니다.
{% endstep %}

{% step %}
## 재구축된 테이블의 제자리 기록 또는 추가 `PF_R` `PT_LOAD` 배치

재구축된 `.dynsym`, `.gnu.version`, 해시 테이블, `.dynstr`, `.rela.dyn`, `.rela.plt`가 `.dynsym`부터 시작하는 기존 파일 영역 안에 모두 들어가면 제자리에 기록합니다. 확장된 재배치 테이블과 심볼 테이블이 기존 영역을 초과하면 기존 `PT_LOAD` 세그먼트의 최대 `p_align`에 맞춰 정렬된 읽기 전용(`PF_R`) `PT_LOAD` 세그먼트를 파일 끝에 추가하고, `DT_SYMTAB`, `DT_STRTAB`, `DT_STRSZ`, `DT_GNU_HASH` / `DT_HASH`, `DT_VERSYM`, `DT_RELA`, `DT_RELASZ`, `DT_JMPREL`, `DT_PLTRELSZ`를 갱신합니다.

매핑된 바이트를 덮어쓰지 않고 추가 `Elf64_Phdr` 엔트리를 삽입하기 위해, 프로그램 헤더 테이블 뒤쪽에 여유 공간이 있으면 이를 우선 활용하고, 그렇지 않으면 `PT_LOAD` 내부의 중복 `PT_NOTE` 헤더(`PT_NOTE` 헤더가 2개 이상일 때)를 재사용하거나 프로그램 헤더 테이블을 새로 추가한 `PT_LOAD`의 시작 부분으로 옮긴 뒤 `e_phoff`와 `PT_PHDR`을 갱신합니다.
{% endstep %}
{% endstepper %}
