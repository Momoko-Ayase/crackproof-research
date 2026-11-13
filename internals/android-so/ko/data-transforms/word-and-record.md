---
description: "GF(2³²) 고정 곱셈과 스트림 헤더, 레코드 디스크립터, 0x9D 암호 구조"
icon: rotate
---

# 워드, 스트림 및 레코드 암호

Android 스트림은 Windows 버전의 롤링 XOR 연산 대신 GF(2³²) 곱셈과 부호 없는 32비트 래핑 연산을 사용하여 스트림 헤더, `0x5C`바이트 레코드 디스크립터, `0x9D` 보호 디스크립터를 암호화합니다.

## GF(2³²) 고정 곱셈

`gf32_mul_fixed(value)`는 입력값을 32비트로 마스킹한 뒤, 환원 다항식 `0x579357EB`를 사용하는 GF(2³²)에서 `0x94511DD2`를 곱합니다.

```text
MASK32 = 0xFFFFFFFF

def gf32_mul_fixed(value):
    value &= MASK32
    multiplier = 0x94511DD2
    result = 0
    while multiplier:
        if multiplier & 1:
            result ^= value
        carry = value >> 31
        value = (value << 1) & MASK32
        if carry:
            value ^= 0x579357EB
        multiplier >>= 1
    return result
```

스트림, 디스크립터 및 [컨테이너 헤더](container.md) 수식에서 `gf(x)`는 `gf32_mul_fixed(x)`를 뜻합니다.

## Stage 1 워드 암호

32바이트 Stage 1 파라미터 헤더와 암호화된 Stage 2 이미지는 모두 워드 인덱스 `i`와 계열 상수 `C`(`0xBF20165D` 또는 `0xBF189BDD`)를 사용한 부호 없는 32비트 래핑 연산으로 복호화합니다.

```text
plain[i] = ((cipher[i] + (i + 3) * key) ^ (C * (i + 1))) & MASK32
```

32바이트 파라미터 헤더에서는 워드 `0`에서 `key = cipher[0] ^ C`를 구해 워드 `1..7`을 복호화한 뒤 `plain[0] = key`를 기록합니다. 헤더 필드의 검증 불변식은 [Stage 1 헤더](../file-format/stage1.md)에 정리되어 있습니다.

## 스트림 헤더 암호

모든 인터프리터 스트림(루트 `0xE2`, 중첩 단계 `0xE3`..`0xE8`)은 리틀 엔디안 dword 두 개(`cipher0`, `cipher1`)로 시작합니다. 현재까지 두 가지 상수 계열이 확인되었으며, 두 계열 모두 중간 곱셈과 덧셈 결과를 32비트로 마스킹하여 `dw0`(레코드 개수) 및 `G`(스트림 디스크립터 시드)를 도출합니다.

{% tabs %}
{% tab title="계열 A" %}
```text
K   = (sid * 0x9D323CD7) & MASK32
K   = ((K << (sid & 0xB)) + (K >> (sid & 7))) & MASK32
dw0 = (gf((cipher0 + 0xCBF0C1D8) & MASK32) ^ ((K + 0x4178CB33) & MASK32)) & MASK32
dw1 = (gf((cipher0 + cipher1) & MASK32)    ^ ((K + 0xF119421B) & MASK32)) & MASK32
G   = (K + 0x5590AD79 + dw1) & MASK32
```
{% endtab %}

{% tab title="계열 B" %}
```text
K   = (sid * 0x9D323CD7) & MASK32
mix = ((K >> (sid & 7)) + 0x5E727D74) & MASK32
mix = (mix + ((K << (sid & 0xB)) & MASK32) + 0xF71E3005) & MASK32
dw0 = (gf((cipher0 + 0xCBF0C1D8) & MASK32) ^ ((0xEBE81DBA + mix) & MASK32)) & MASK32
dw1 = (gf((cipher1 + cipher0) & MASK32)    ^ ((0xEBE81DBA * 5 + mix) & MASK32)) & MASK32
G   = (dw1 + mix) & MASK32
```
{% endtab %}
{% endtabs %}

두 상수 계열을 차례로 적용해 [Stage 2 스트림](../file-format/stage2-streams.md)의 구조적 디스크립터 검증을 통과하는 쪽을 채택합니다.

## 레코드 디스크립터 암호

각 `0x5C`바이트 레코드 디스크립터는 23개의 리틀 엔디안 dword로 이루어집니다. 스트림 시드 `G`와 0부터 시작하는 레코드 인덱스 `idx`가 주어졌을 때, 두 상수 계열 모두 동일한 복호화 루프를 사용합니다.

```text
def rec_decrypt(G, idx, rec):
    product = ((G + 0x96F60B71) * G) & MASK32
    record_mask = (product << ((idx + 1) & 3)) & MASK32
    stream_mix = (G * 0x06A55BCC + product) & MASK32
    feedback = 0xF02F7685
    acc = 0x79934CF6
    for off in range(0, 0x5C, 4):
        cipher = get_u32(rec, off)
        square = (feedback * feedback) & MASK32
        value = gf32_mul_fixed(cipher ^ (square >> 3))
        value = (value ^ record_mask) & MASK32
        value = (value + acc + G) & MASK32
        value = (value - (stream_mix >> ((off + 3) & 5))) & MASK32
        put_u32(rec, off, value)
        acc = (acc + 0xE64D33D8) & MASK32
        feedback = cipher
```

{% hint style="warning" %}
`off`는 반복마다 4바이트씩 증가하므로 `(off + 3) & 5`는 짝수 인덱스 워드에서 `1`(`(0 + 3) & 5 = 1`), 홀수 인덱스 워드에서 `5`(`(4 + 3) & 5 = 5`)로 번갈아 바뀝니다. 또한 `feedback`은 복호화된 `value`가 아니라 원본 암호문 워드인 `cipher`로 갱신됩니다.
{% endhint %}

## `0x9D` 보호 디스크립터

직접 모듈 `0x9D`는 [모듈 `0x9B`](module-config.md)의 `header_seed`로 암호화된 `0x5C`바이트 크기의 `ProtectedDescriptor`로 시작합니다.

```text
def decrypt_protected_descriptor(data, seed):
    base0 = ((seed + 0xD3E87144) * seed) & MASK32
    base1 = (base0 + seed * 0x0BD9418D) & MASK32
    words = [0] * (0x5C // 4)
    for i in range(len(words)):
        cipher = get_u32(data, i * 4)
        sub = (base0 << (4 if i & 1 else 0)) & MASK32
        words[i] = ((cipher - sub) ^ (base1 >> ((seed + i * 4) & 7))) & MASK32
    return words
```

유효한 평문은 `words[0] == 0x9D`(`command_id`), `words[2] == 0x5C`(디스크립터 직후를 가리키는 `outer_offset`), `words[6..23] == 0` 조건을 만족해야 합니다. 워드 `2..5`는 기본 ELF 이미지 컨테이너의 `(outer_offset, outer_size)`와 [컨테이너 변환](container.md)에서 설명하는 보조 재배치 및 심볼 컨테이너의 `(aux_offset, aux_size)`를 지정합니다.
