---
description: "0x8003 LFSR 스텁 암호, RVA 기반 임포트 문자열 암호 및 페이지 스크램블"
icon: wave-square
---

# LFSR, 문자열 및 페이지 변환

## LFSR 키스트림 (`dd6`) <a href="#lfsr-keystream-dd6" id="lfsr-keystream-dd6"></a>

96바이트 크기의 각 [빌드별 바이트코드 스텁](bytecode-transform.md) 슬롯은 `pos + 95` 위치에 암호화되지 않은 프로그램 길이(`<= 95`)를 저장하며, 고정 시드 갈루아(Galois) LFSR(초기 상태 `1`, 다항식 `0x8003`, 바이트당 8비트를 LSB 우선으로 출력)로 `d[pos .. pos + length]` 구간을 마스킹합니다.

```python
def lfsr_keystream(n):
    out = bytearray(n)
    state = 1
    for i in range(n):
        b = 0
        for k in range(8):
            b |= (state & 1) << k
            state = (state << 1) & MASK32
            if state & 0x8000:
                state ^= 0x8003
        out[i] = b
    return out

def lfsr_decrypt_block(d, pos):
    """XOR a bytecode stub with the keystream. The block length is stored
    unencrypted at pos+95."""
    length = d[pos + 95]
    ks = lfsr_keystream(length)
    for i in range(length):
        d[pos + i] ^= ks[i]
```

키스트림이 바이트 오프셋 `0..length`에만 의존하므로, 미리 계산한 95바이트 키스트림 테이블을 사용하면 임의의 오프셋에서 96바이트 후보 윈도우를 즉시 검사할 수 있습니다.

## 임포트 이름 문자열 암호 (`dd7`)

암호화된 DLL 이름과 임포트 심볼 이름은 NUL 종료 롤링 바이트 암호를 사용합니다. 상위/하위 니블을 맞바꾸고(`ror8(..., 4)`), `key`를 뺀 결과가 `0`이면 문자열 중간 바이트가 조기 NUL 종료 문자가 되지 않도록 `(-key) & 0xFF`로 치환한 뒤, 매 바이트마다 `key`를 `67`씩 증가시킵니다.

```python
def string_cipher(d, pos, key):
    """Decrypt a NUL-terminated string in place."""
    i = 0
    while d[pos + i] != 0:
        b = ror8(d[pos + i], 4)
        b = (b - key) & 0xFF
        if b == 0:
            b = (-key) & 0xFF
        d[pos + i] = b
        key = (key + 67) & 0xFF
        i += 1
```

{% hint style="warning" %}
**DLL 이름과 함수 이름의 초기 `key` 차이.** `name_rva`에 위치한 DLL 이름은 `pos = name_rva`, `key = name_rva & 0xFF`로 시작합니다. 반면 이름 기반(by-name) 임포트는 `hint_name_rva`에 있는 `IMAGE_IMPORT_BY_NAME` 레코드를 가리키며, ASCII 심볼 문자열 앞에 2바이트 `Hint` 필드가 놓입니다. 따라서 복호화는 `pos = hint_name_rva + 2`에서 시작하지만, 초기 키는 `(hint_name_rva + 2) & 0xFF`가 아니라 레코드 시작 RVA 기준인 `hint_name_rva & 0xFF`를 그대로 사용합니다.
{% endhint %}

## 페이지 단위 코드 스크램블 (`dd8`)

실행 코드 섹션에는 선택적으로 희소(sparse) XOR 패스가 한 겹 더 적용됩니다. 이 패스는 4,096바이트 페이지마다 16바이트 블록 `1..255`에서 각각 1바이트씩(페이지당 총 255바이트) 선택해 `key & 0xFF`를 XOR하며, 블록 `0`은 바이트를 수정하지 않고 `key`만 갱신합니다.

```python
def page_scramble(d, va, size, key):
    """64-bit form. `key` is the absolute page index shifted left by a
    build-specific amount (0 or 15)."""
    for i in range(size >> 4):
        mixed = (ror32(key, 15) + i) & MASK32
        key = (mixed + i) & MASK32
        if i == 0:
            continue
        d[va + i * 16 + (mixed & 0xF)] ^= key & 0xFF

def page_scramble_pe32(d, pa, page, big_formula):
    """32-bit form. The page key is (page+1) or 0x8000*(page+1)."""
    key = (0x8000 * (page + 1)) & MASK32 if big_formula else page + 1
    key = ror32(key, 15)
    for bi in range(1, 256):
        rk = ror32(key, 15)
        ri = (rk + bi) & MASK32
        key = (ri + bi) & MASK32
        d[pa + bi * 16 + (ri & 0xF)] ^= key & 0xFF
```

{% hint style="info" %}
**스크램블 모드 판별 방법.** 64비트 시프트 값(`0`, `15`, 또는 변환 없음)이나 32비트 수식(`page + 1`, `0x8000 * (page + 1)`, 또는 변환 없음)은 컨테이너 헤더에 기록되어 있지 않으며, 상당수 네이티브 DLL은 `.text`에 스크램블을 적용하지 않습니다.
1. **64비트 CRT 엔트리 검사:** 18바이트 MSVC 엔트리 스텁(`48 83 EC ib / E8 rel32 / 48 83 C4 ib / E9 rel32`, 두 스택 즉시값이 일치하는 패턴)을 '변환 없음', 시프트 `0`, 시프트 `15` 세 모드에 대해 검사합니다. `call` 및 `jmp` 대상 주소가 모두 `.text` 내부에 들어오는 모드가 유일하면 해당 모드를 즉시 선택합니다.
2. **64비트 `RET` + `int3` 에필로그 점수:** 위 조건으로 결정되지 않으면 `.text` 내부 페이지들을 샘플링하여 `0xC3` (`RET`) 뒤에 4바이트 이상의 `0xCC` 패딩이 이어지는 구간의 총 바이트 길이를 합산하고, 변환하지 않은 기준선(baseline)보다 `8`바이트 이상 증가하는 모드를 선택합니다.
3. **변경 바이트 `0xCC` 폴백 (64비트 및 32비트):** 64비트에서 모든 `RET + int3` 점수가 0인 경우에만(32비트에서는 항상 적용), 스크램블 해제 시 값이 `0xCC`로 바뀌는 변경 위치의 개수를 세어 기준선의 `2`배 이상이면서 `8`개 이상일 때만 채택하고, 그렇지 않으면 `.text`를 그대로 유지합니다.
{% endhint %}
