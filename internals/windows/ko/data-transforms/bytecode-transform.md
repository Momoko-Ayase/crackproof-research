---
description: "빌드별 9종 AL x86 바이트코드 스텁과 256바이트 LUT 사전 계산 및 스텁 탐색"
icon: microchip
---

# 빌드별 바이트 변환

## 빌드별 `AL` 바이트코드 순열 변환

패킹 시점에 CrackProof는 `AL` 레지스터로 1바이트를 입력받아 무작위로 조합된 산술 및 비트 회전 명령어 체인을 적용한 뒤 반환(`RET`)하는 짧은 빌드별 x86 함수 두 개를 합성합니다. 첫 번째 스텁은 마지막 로더 스테이지를 디코딩하고, 두 번째 스텁은 AES-CBC 복호화와 허프만/LZ 압축 해제 사이에서 모든 섹션 페이로드 블록을 디코딩합니다.

각 스텁은 [LFSR 키스트림](lfsr-strings-pages.md#lfsr-keystream-dd6)으로 마스킹된 96바이트 슬롯을 차지하며, 슬롯의 `+95` 오프셋에는 암호화되지 않은 프로그램 바이트 길이가 저장되어 있습니다. 스텁 내부에는 다음 9가지 x86 명령어 인코딩만 등장합니다.

| 바이트 | x86 명령어 | 디코딩된 연산 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | 건너뜀 |
| `C0 C0 ib` (`mod=3, reg=0, rm=0`) | `ROL AL, imm8` | `("rol", imm)` |
| `C0 C8 ib` (`mod=3, reg=1, rm=0`) | `ROR AL, imm8` | `("ror", imm)` |
| `FE C0` (`mod=3, reg=0, rm=0`) | `INC AL` | `("inc",)` |
| `FE C8` (`mod=3, reg=1, rm=0`) | `DEC AL` | `("dec",)` |
| `C3` | `RET` | 프로그램 종료 |

이 외의 옵코드나 허용되지 않은 `ModR/M` 바이트가 나타나면 해당 후보 슬롯은 기각됩니다.

```python
def generate(data, offset=0):
    """Decode the stub at `offset` into an op list, or return None if the
    byte stream is not a valid stub (must terminate in RET)."""
    pos = offset
    ops = []

    def take():
        nonlocal pos
        if pos >= len(data):
            return None
        b = data[pos]
        pos += 1
        return b

    while True:
        op = take()
        if op is None:
            return None
        if op == 0x04:
            imm = take()
            if imm is None:
                return None
            ops.append(("add", imm))
        elif op == 0x2C:
            imm = take()
            if imm is None:
                return None
            ops.append(("sub", imm))
        elif op == 0x34:
            imm = take()
            if imm is None:
                return None
            ops.append(("xor", imm))
        elif op == 0x90:
            pass
        elif op in (0xC0, 0xFE):
            modrm = take()
            if modrm is None:
                return None
            mod, reg, rm = modrm >> 6, (modrm >> 3) & 7, modrm & 7
            if mod != 3 or rm != 0 or reg > 1:
                return None
            if op == 0xC0:
                imm = take()
                if imm is None:
                    return None
                ops.append(("rol" if reg == 0 else "ror", imm))
            else:
                ops.append(("inc" if reg == 0 else "dec",))
        elif op == 0xC3:
            return ops
        else:
            return None

def apply_ops(ops, x):
    """Run an op chain over a single byte."""
    for op in ops:
        name = op[0]
        if name == "add":
            x = (x + op[1]) & 0xFF
        elif name == "sub":
            x = (x - op[1]) & 0xFF
        elif name == "xor":
            x ^= op[1]
        elif name == "rol":
            n = op[1] & 7
            x = ((x << n) | (x >> (8 - n))) & 0xFF
        elif name == "ror":
            n = op[1] & 7
            x = ((x >> n) | (x << (8 - n))) & 0xFF
        elif name == "inc":
            x = (x + 1) & 0xFF
        elif name == "dec":
            x = (x - 1) & 0xFF
    return x
```

## 전단사 성질과 스텁 탐색 규칙

* **256바이트 룩업 테이블:** `AL`에 적용되는 모든 연산은 역연산이 존재하므로(`add <-> sub`, 자기 역원인 `xor`, `rol <-> ror`, `inc <-> dec`), 유효한 바이트코드 프로그램은 항상 `0..255` 구간의 전단사 함수(bijection)를 이룹니다. 따라서 실행 전에 `lut = bytes(apply_ops(ops, i) for i in range(256))` 형태로 256바이트 변환 테이블을 미리 계산해 둘 수 있습니다.
* **빌드 계열별 스텁 위치:**
  * **전용 64비트 DLL:** 고정 오프셋에 위치합니다(스텁 1은 `addr4 + 3200`, 스텁 2는 `addr5 + 12400`).
  * **64비트 Stage 4 / 구형 마커 Stage 5:** 16바이트 간격으로 LFSR 복호화 스캔을 수행하며, `NOP` 이외의 유효 명령어를 충분히 포함한 첫 번째 파싱 결과를 스텁으로 채택합니다.
  * **PE32 `SevenStage`:** `seven_dsz - 96`에서 `seven_dsz / 2`까지 역방향으로 먼저 스캔하고, 찾지 못하면 순방향 스캔으로 전환합니다.
  * **마커리스 64비트 Stage 5 및 PE32 `EighthStage`:** 1바이트 단위로 LFSR 스캔을 진행합니다. 실제 스텁보다 **앞쪽**에서 우연히 문법 조건을 만족하는 짧은 바이트열이 먼저 잡힐 수 있으므로, `fileCS` 포인터와의 거리(64비트 기준 `stub - 0x58`)를 확인하고 첫 번째 압축 섹션 블록을 `decompress`에 통과시켜 실제 스텁을 판별합니다.
