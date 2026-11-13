---
description: "시드 기반 5라운드 MethodDef RID 순열(v29/v31/v39) 및 v24.1 복원"
icon: hashtag
---

# 메서드 토큰

표준 IL2CPP 메타데이터 파일은 매직 넘버 `0xFAB11BAF`와 32비트 버전 번호로 시작합니다. Android에서 CrackProof는 버전 `29`, `31`, `39`의 `Il2CppImage`별 `MethodDef` RID(`0x06000000 | rid`)와 버전 `24`(`v24.1`)의 전역 `methodIndex` 엔트리(256엔트리 예외 테이블과 함께 구성)에 시드 기반 5라운드 산술 반전·감산(mirror-and-subtract) 순열을 적용합니다. 일부 버전 `31` 빌드는 키 없이 동작하는 `-GMD` 토큰 레이아웃을 대신 사용합니다.

테이블 순서만으로 띄엄띄엄 배치된 토큰을 `0x06000000 | (local_index + 1)`로 재매핑하는 키 없는 Windows `-GMD` 방식과의 비교는 [IL2CPP 메타데이터 난독화](https://app.gitbook.com/s/FlY9nVrA6FxLQBrkLIc2/analysis/il2cpp-metadata)를 참고하십시오.

## 5라운드 역순열

연속된 `count`개 엔트리 구간(`count >= 2`)과 32비트 `seed`가 주어지면 `key = (seed % (count // 2)) + (count // 4)` 및 산술 반전 상수 `mirror = count * 2 - 1`을 계산합니다. 0부터 시작하는 각 오프셋 `value`(`0 <= value < count`)는 부호 없는 32비트 래핑 연산(`MASK32 = 0xFFFFFFFF`)을 사용하는 동일한 5라운드를 거쳐 역변환됩니다.

```text
repeat 5 times:
    if value & 1:
        value = mirror - value
    value >>= 1
    if value >= count:
        value = mirror - value
    value = (value - key) & MASK32
    if value > count:
        value = (value + count) & MASK32
```

버전 `29`, `31`, `39`의 `MethodDef` 토큰에서는 각 `Il2CppImage`의 닫힌 RID 구간 `[low, high]` 안에서 `value = rid - low`로 두며, 복원된 메서드 토큰은 `0x06000000 | (value + low)`가 됩니다. 정규(canonical) 메타데이터는 이미 `Il2CppImage`별로 `1..=count`의 순차 RID를 가지므로, 복원 시에는 각 `Il2CppImage`가 이미 정규 순서인지 먼저 확인하여 난독화되지 않은 원본 입력을 그대로 보존합니다.

## 버전별 레이아웃 및 시드 복원

{% tabs %}
{% tab title="버전 29 및 31" %}
버전 `29`와 `31`은 고정된 헤더 `{offset, size}` 쌍을 사용하며 타입 및 이미지 디스크립터 구조를 공유합니다.

* **타입(`@0xA0`, 보폭 `0x58`):** `+0x24`의 `methodStart`(`u32`), `+0x40`의 `method_count`(`u16`).
* **이미지(`@0xA8`, 보폭 `0x28`):** `+0x08`의 `typeStart`(`u32`), `+0x0C`의 `typeCount`(`u32`).
* **메서드(`@0x30`):**
  * **버전 29:** 보폭 `0x20`, `+0x14`의 `token`(`u32`).
  * **버전 31:** 보폭 `0x24`, `+0x18`의 `token`(`u32`).

런타임에는 모듈 `0x0C`가 `mmap`을 후킹하여 내장된 시드(확인된 기본 빌드에서는 `0xA6FAE968`)를 적용합니다. 그러나 버전 `29`, `31`, `39`의 정적 복원에는 모듈 `0x0C`가 필요하지 않습니다. 각 `Il2CppImage`에서 가능한 `key` 나머지(residue) 후보가 `count / 2`개뿐이므로, `1..=count` 정규 순서가 나오는 후보를 시험하고 `Il2CppImage` 간 `seed % (count / 2)` 제약 조건의 교집합을 구하면 `global-metadata.dat` 파일만으로도 유효한 시드를 직접 복원할 수 있습니다. 제약 조건이 남지 않는 파일은 기본 시드 `0xA6FAE968`을 사용하며, `-GMD`로 보호된 버전 `31` 빌드는 테이블 순서에 따라 `0x06000000 | (local_index + 1)`로 재매핑하는 폴백을 대신 수행합니다.
{% endtab %}

{% tab title="버전 39 (압축 디렉터리)" %}
버전 `39`는 고정 헤더 오프셋 대신 12바이트 `{offset, size, count}` 섹션 디스크립터로 구성된 압축 디렉터리와 가변 폭 테이블 인덱스를 사용합니다.

* `type_definition`, `parameter`, `generic_container` 인덱스의 폭은 `count <= 255`일 때 `1`바이트, `count <= 65535`일 때 `2`바이트, `count > 65535`일 때 `4`바이트입니다.
* `type_index`의 폭은 섹션 `18`(`interface_offsets`)에서 유도되며, `count == 0`이면 `4`바이트이고 그 외에는 `(size / count) - 4`입니다.

이 네 가지 인덱스 폭으로부터 메서드, 타입, 이미지 레코드의 보폭과 필드 오프셋을 계산한 뒤에는 동일한 `Il2CppImage`별 나머지 탐색과 5라운드 RID 역순열을 그대로 수행합니다.
{% endtab %}

{% tab title="버전 24.1 (methodIndex + 0x0C)" %}
`v24.1`의 `Il2CppMethodDefinition` 레이아웃(보폭 `0x34`, `+0x14`에 부호 있는 `i32` `methodIndex`)을 따르는 외부 버전 `24` 메타데이터는 `MethodDef` 토큰을 건드리지 않고, 음수가 아닌 모든 `methodIndex` 엔트리(`0..active_count`, 단 `active_count > 256`)를 순열로 뒤섞습니다.

1. 음수가 아닌 `active_count`개의 `methodIndex` 슬롯 전체에 `key = (seed % (active_count // 2)) + (active_count // 4)`를 사용한 5라운드 함수를 적용하여 순열을 수행합니다.
2. 상위 256개 활성 슬롯의 값은 모듈 `0x0C` 내부의 256엔트리 `u32` 예외 테이블에 별도로 저장합니다.

따라서 정적 복원 시에는 메타데이터 파일을 동일 애플리케이션에서 디코딩한 모듈 `0x0C`와 짝지어, `0x0C` 내부에서 `{u32 seed, u32 24}` 및 `{u32 1, u32 active_count - 1}` 헤더 마커와 256엔트리 예외 테이블을 찾은 뒤 256개 예외 항목을 복원하고 전체 `active_count`개 활성 메서드에 대해 5라운드 역순열을 수행합니다.
{% endtab %}
{% endtabs %}

## 복원 후 검증

재매핑이 끝나면 이미지, 타입, 메서드 테이블이 파일 범위 안에 들어가는지, 모든 메서드가 연속된 테이블 순서로 정확히 하나의 `Il2CppImage`에 속하는지, 모든 `MethodDef` 토큰이 `0x06000000` 테이블 접두사와 정규 로컬 RID(또는 `v24.1`의 경우 `0..active_count` 전체 범위)를 갖는지, 그리고 범위를 벗어나거나 중복된 엔트리가 없는지 검증합니다.
