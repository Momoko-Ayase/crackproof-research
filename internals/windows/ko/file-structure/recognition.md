---
description: "콘텐츠 기반 KONN 탐지, 네이티브/관리형 PE 분류 및 레이아웃 계열"
icon: fingerprint
---

# 포맷 식별 및 빌드 계열

## 콘텐츠 기반 식별 및 모듈 분류

다음 두 조건을 만족하면 외부 컨테이너 시그니처와 일치하는 파일로 판별합니다.

1. 파일 길이가 `4128`바이트(`0x1020`) 이상이고, `e_lfanew` (`u32@0x3C`)가 유효한 `PE\0\0` 시그니처를 가리킵니다.
2. 오프셋 `4096`에서 실행한 `header_kdf` 결과가 `info[1] == 0x4E4E4F4B` (`KONN`)입니다.

두 검사를 통과하면 후보 컨테이너로 식별되며, 완전한 검증을 위해서는 `info` 범위의 유효성, 스테이지 디스크립터 정합성, 스테이지 체크섬 통과 여부 또는 시험 압축 해제(trial decompression)까지 확인해야 합니다.

컨테이너가 식별되면 표준 PE 헤더 필드를 기준으로 대상 모듈을 네 가지 종류로 분류합니다.

* `IMAGE_FILE_HEADER.Characteristics & 0x2000` (`IMAGE_FILE_DLL`) 플래그로 DLL과 EXE를 구분합니다.
* 데이터 디렉터리 `14` (`IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR`, 옵션 헤더 기준 PE32는 `+96`, PE32+는 `+112`에서 데이터 디렉터리 배열 시작)로 관리형(.NET) 어셈블리와 네이티브 바이너리를 구분합니다.

| `IMAGE_FILE_DLL` | CLR RVA (`DD[14]`) | 모듈 종류 |
| --- | --- | --- |
| `0` | `0` | `native-exe` |
| `0` | 0이 아님 | `managed-exe` |
| 0이 아님 | `0` | `native-dll` |
| 0이 아님 | 0이 아님 | `managed-dll` |

관리형 EXE는 네이티브 EXE와 동일한 EXE 스타일 컨테이너를 사용합니다.

```python
MAGIC_KONN = 0x4E4E4F4B  # the shell stamp

def detect(file_data):
    """Return ("native-exe" | "managed-exe" | "native-dll" | "managed-dll",
    magic) for a protected file, or None when the file is not protected by
    this scheme."""
    if len(file_data) < 4128:
        return None
    pe_off = get_u32(file_data, 0x3C)
    if file_data[pe_off:pe_off + 4] != b"PE\0\0":
        return None
    info = header_kdf(file_data)
    if info[1] != MAGIC_KONN:
        return None

    characteristics = get_u16(file_data, pe_off + 4 + 18)   # IMAGE_FILE_HEADER
    is_dll = bool(characteristics & 0x2000)                 # IMAGE_FILE_DLL

    # COM descriptor (CLR) data directory: managed vs native, EXE and DLL alike.
    # Data directories start at optional-header +96 on PE32, +112 on PE32+.
    opt_magic = get_u16(file_data, pe_off + 24)             # 0x10B / 0x20B
    dd_base = 112 if opt_magic == 0x20B else 96
    clr_rva = get_u32(file_data, pe_off + 24 + dd_base + 14 * 8)
    managed = bool(clr_rva)

    if is_dll:
        return ("managed-dll" if managed else "native-dll", info[1])
    return ("managed-exe" if managed else "native-exe", info[1])
```

{% hint style="info" %}
데이터 디렉터리를 인덱싱하기 전에 옵션 헤더 매직(`0x10B` 또는 `0x20B`)을 먼저 확인해야 합니다. `DD[14]`는 PE32에서 `pe + 0xE8`, PE32+에서 `pe + 0xF8`에 위치하므로 오프셋을 잘못 읽으면 32비트 네이티브 바이너리를 관리형 어셈블리로 오분류할 수 있습니다.
{% endhint %}

## 확인된 레이아웃 분류 축

보호된 Windows 파일은 네 가지 구조적 축에 따라 나뉩니다(모든 조합이 존재하지는 않으며, 전용 DLL 컨테이너는 64비트 마커 레이아웃에서만 나타나고 외부 컴패니언은 PE32+ EXE 스타일 셸을 사용합니다).

* **비트 폭:** PE32+ (`0x20B`, 64비트)와 PE32 (`0x10B`, 32비트)는 `header_kdf`와 핵심 암호 알고리즘을 공유하지만, 설정 테이블 구조, 스테이지 수, 임포트 및 헤더 복원 규칙이 서로 다릅니다(PE32는 표준형과 컴팩트 셸 변형으로 다시 나뉩니다).
* **모듈 종류:** `native-exe`, `managed-exe`, `native-dll`, `managed-dll` 네 가지로 구분됩니다. 관리형 빌드에서 디스크 상의 `COR20` 헤더와 `BSJB` 메타데이터 루트가 평문으로 남아 있더라도, 실제 IL 메서드 본문은 암호화 및 압축된 섹션 페이로드 내부에 들어 있습니다.
* **64비트 설정 탐색 방식:**
  * **마커 레이아웃(구형):** 스테이지 5 내부에 리터럴 마커 `70 6D 00 00 63 6D 00 00` (`"pm\0\0cm\0\0"`)과 `00 00 00 40 01 00 00 00` (`0x40000000, 1`)이 포함되어 있어 고정 상대 오프셋에서 디스크립터 테이블을 찾을 수 있습니다.
  * **마커 없는 레이아웃(신형):** 두 리터럴 마커가 생략되며, LFSR 스캔, `trial_byte_rotate2` 범위 검사, `fileCS` 거리 점수화, 시험 압축 해제를 조합해 스테이지 5 슬롯과 바이트코드 스텁 위치를 찾습니다.
* **DLL 컨테이너 형태:**
  * **전용 DLL 레이아웃:** 설정 테이블이 고정 오프셋 `info[6] + 5592` (`0x15D8`)에서 시작하는 64비트 DLL 전용 컨테이너(`0x20B`)입니다.
  * **EXE 스타일 셸:** EXE에 쓰이는 것과 동일한 단계별 셸로 32비트 또는 64비트 DLL을 감싸는 방식이며, 선택적으로 [외부 컴패니언(`._`)](companion-layout.md) 분할을 함께 사용합니다.
