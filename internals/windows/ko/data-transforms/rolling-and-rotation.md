---
description: "롤링 XOR 페이로드 체인, XOR-회전 dword 블록 및 3중 바이트 회전 암호"
icon: rotate
---

# 롤링 키 및 회전 암호

스테이지 헤더와 포인터 테이블은 8비트 및 32비트 부호 없는 래핑 연산으로 구성된 네 가지 소형 제자리(in-place) 암호를 사용합니다.

{% hint style="success" %}
이 페이지의 모든 Python 함수는 `verification/verify_docs.py`를 통해 자동으로 실행되며, 독립된 레퍼런스 테스트 벡터와 바이트 단위로 일치하는지 검증됩니다.
{% endhint %}

## 공통 비트 폭 헬퍼

모든 함수는 변경 가능한 `bytearray` 버퍼를 제자리에서 직접 수정합니다.

```python
MASK32 = 0xFFFFFFFF

def get_u16(d, off):
    return d[off] | (d[off + 1] << 8)

def get_u32(d, off):
    return d[off] | (d[off + 1] << 8) | (d[off + 2] << 16) | (d[off + 3] << 24)

def put_u32(d, off, value):
    d[off:off + 4] = (value & MASK32).to_bytes(4, "little")

def rol32(x, n): return ((x << n) | (x >> (32 - n))) & MASK32
def ror32(x, n): return ((x >> n) | (x << (32 - n))) & MASK32
def rol8(x, n):  return ((x << n) | (x >> (8 - n))) & 0xFF
def ror8(x, n):  return ((x >> n) | (x << (8 - n))) & 0xFF
```

## 페이로드 롤링 XOR 체인

`header_kdf`([컨테이너 및 암호화된 헤더](../file-structure/container-layout.md) 참고)와 `payload_xor_chain`은 동일한 인덱스 제곱 피드백 구조를 공유하며, `- i` 대신 `+ i`를 사용하고 초기 시드로 `info[0] + ~decrypt_size`를 잡는 점만 다릅니다.

```python
def payload_xor_chain(file_data, out, info, decrypt_size):
    """Decrypt the bulk of the payload into the image buffer."""
    base_src = (info[4] + 4096) & MASK32
    k = (info[0] + (~decrypt_size & MASK32)) & MASK32
    for i in range(decrypt_size >> 2):
        cell = get_u32(file_data, (base_src + 4 * i) & MASK32)
        put_u32(out, (info[3] + 4 * i) & MASK32, k ^ cell)
        k = (i * i) ^ ((k + cell + i) & MASK32)
```

`k`가 매 단계의 암호문 dword인 `cell`을 누적 반영하므로, 복호화는 반드시 정확한 `decrypt_size` (`info[6] - info[3] + 8192`, 또는 전체 페이로드를 암호화하는 컴팩트 PE32 빌드에서는 `info[5]`)를 사용해 `i = 0`부터 시작해야 합니다.

## XOR 및 우측 회전 dword 암호 (`dd3`)

이 프리미티브는 `pos` 위치에서 `{base_addr, length}`를 읽은 뒤, 각 dword를 `key`와 XOR하고 `shift`비트(64비트 스테이지에서는 `19` 또는 `21`)만큼 우측 회전한 값에서 dword 인덱스 `i`를 뺍니다.

```python
def xor_ror_dwords(d, pos, key, shift):
    base_addr = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    for i in range(length >> 2):
        off = (base_addr + 4 * i) & MASK32
        v = get_u32(d, off) ^ key
        key = (key + i) & MASK32
        put_u32(d, off, (ror32(v, shift) - i) & MASK32)
```

PE32 빌드는 한 스테이지에 대해 8개의 비트 회전 수 후보 `[19, 21, 17, 23, 15, 25, 13, 11]`을 순서대로 대입해 시험 복호화하며, 후속 스테이지 테이블 검증을 통과하는 값을 채택합니다([PE32, DLL 및 마커 없는 레이아웃](../loading-and-pe-repair/loading/layout-variants.md) 참고).

## 3중 바이트 회전 암호 (`dd4` 및 `dd5`)

두 바이트 암호는 각 바이트를 좌측으로 세 번 회전하면서 회전 사이에 1씩 증가하는 두 개의 키 바이트를 XOR합니다.

```python
def byte_rotate3(d, pos):
    """Descriptor-addressed variant: rotate by 3, keyed from the address."""
    base_addr = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    b = ((base_addr >> 8) + base_addr) & 0xFF
    b2 = (b + 1) & 0xFF
    for i in range(length):
        idx = base_addr + i
        x = rol8(d[idx], 3) ^ b2
        x = rol8(x, 3) ^ b
        d[idx] = rol8(x, 3)
        b = (b + 1) & 0xFF
        b2 = (b2 + 1) & 0xFF

def byte_rotate2(d, va, size):
    """Position-keyed variant: rotate by 2, keyed from the address itself."""
    b = va & 0xFF
    b2 = (b + 1) & 0xFF
    for i in range(size):
        idx = va + i
        x = rol8(d[idx], 2) ^ b2
        x = rol8(x, 2) ^ b
        d[idx] = rol8(x, 2)
        b = (b + 1) & 0xFF
        b2 = (b2 + 1) & 0xFF
```

`byte_rotate2`에서 `va + i` 위치의 바이트는 이전 바이트 상태와 무관하게 `d[va + i]`와 `(va + i) & 0xFF`만으로 결정되므로, 디스크립터 테이블을 탐색할 때 원본 버퍼를 수정하지 않고 4바이트 시험 복호화를 수행할 수 있습니다.

```python
def trial_byte_rotate2(d, va):
    """Non-mutating 4-byte trial decrypt."""
    out = bytearray(4)
    for i in range(4):
        b = (va + i) & 0xFF
        x = rol8(d[va + i], 2) ^ ((b + 1) & 0xFF)
        x = rol8(x, 2) ^ b
        out[i] = rol8(x, 2)
    return get_u32(out, 0)
```

연속 배치된 16바이트 로더 디스크립터 배열은 각 엔트리의 RVA를 기준으로 `byte_rotate2`로 암호화되어 있으며, `length` 필드가 0인 엔트리에서 끝납니다.
