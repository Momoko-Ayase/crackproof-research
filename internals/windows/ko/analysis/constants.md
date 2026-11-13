---
description: "매직 값, 컨테이너 수식, 암호 연산, PE32/PE32+ 오프셋 및 바이트코드 레퍼런스."
icon: sliders
---

# 상수 및 오프셋

## 컨테이너 상수 및 매직 값

| 항목 | 값 |
| --- | --- |
| 포맷 매직 (`info[1]`) | `0x4E4E4F4B` (리틀 엔디언 ASCII 기준 `KONN`) |
| 외부 PE 헤더 영역 / `info` 오프셋 | `4096` (`0x1000`) |
| 암호화된 `info` 헤더 길이 | `32`바이트 (`8` DWORD) |
| 최소 후보 파일 길이 | `4128` (`0x1020`)바이트 |
| `decrypt_size` (표준 / 전체 페이로드 PE32) | `info[6] - info[3] + 8192` / `info[5]` (컴팩트 PE32 폴백) |
| 섹션 데이터 파일 베이스 | `(~u32@0x1080 + 0x1000) & 0xFFFFFFFF` |
| 동반 파일(`._`) 페어링 검사 | `stub[4096..4128] == companion[0..32]` |
| 동반 파일 엔트리 썽크 마커 (`+53` / `+58`) | `~0x1000` / `~u32("._\0\0")` (단일 파일 PE32+에서는 `~0`) |
| 페이로드 복사 후 `image[info[3]]`에 기록되는 DWORD | `4096` (`0x1000`) |
| PE32 `EighthStage` 클러스터 스탬프 | `0x00007679` (존재하는 경우) |
| 64비트 Stage 5 마커 (기존 레이아웃) | `70 6D 00 00 63 6D 00 00` (`"pm\0\0cm\0\0"`) 및 `00 00 00 40 01 00 00 00` |

## 암호 및 체크섬 요약

| 기본 연산 | 수식 (부호 없는 8/32비트 래핑 연산) |
| --- | --- |
| `header_kdf` | `info[i + 1] = k ^ cell; k = (i * i) ^ ((k + cell - i) & MASK32)` |
| `payload_xor_chain` | `k0 = info[0] + ~decrypt_size; out = k ^ cell; k = (i * i) ^ ((k + cell + i) & MASK32)` |
| `xor_ror_dwords` (`dd3`) | `v = x ^ key; key += i; out = ror32(v, shift) - i` (64비트: `19`/`21`; 32비트: 8종 시프트 집합) |
| `byte_rotate3` (`dd4`) | `b = ((addr >> 8) + addr) & 0xFF; b2 = b + 1`; 3비트 `rol8` 3회 수행 후 `b2`, `b` 순서로 XOR |
| `byte_rotate2` (`dd5`) | `b = va & 0xFF; b2 = b + 1`; 2비트 `rol8` 3회 수행 후 `b2`, `b` 순서로 XOR (이전 바이트와 무관한 바이트별 연산) |
| `lfsr_keystream` (`dd6`) | 시드 `1`, 다항식 `0x8003`, 바이트당 8비트 LSB 우선; 평문 길이는 `pos + 95`에 위치 |
| `string_cipher` (`dd7`) | `ror8(b, 4) - key` (`0 -> -key`), `key += 67`; 키는 `name_rva & 0xFF` 또는 `hint_name_rva & 0xFF` |
| `page_scramble` (`dd8`, 64비트) | `mixed = ror32(key, 15) + i; key = mixed + i`; `i >= 1`에 대해 `page[i * 16 + (mixed & 0xF)] ^= key & 0xFF` |
| `page_scramble_pe32` (`dd8`, 32비트) | 사전 단계 `key = ror32(pk, 15)` (`pk = page + 1` 또는 `0x8000 * (page + 1)`) 수행 후 `i = 1..255` 반복 |
| `crc32` 및 `calculate_checksum` | 반전 CRC-32 (`0xEDB88320`); 영역 체크섬 `crc32(region) ^ length` |
| `advance_key` | `m in 0..iterations`에 대해 `1 .. ((m + 1) * 100)` 합산 |
| `aes_decrypt` | Zero-IV AES-CBC; 라운드 수는 `key_offset + 2`의 `u16`; 빅 엔디언 상태 워드; 표준 GF(2⁸) 역 T-테이블 |

## PE 헤더 오프셋 (`pe = u32@0x3C`)

| 필드 | PE32+ (`0x20B`) | PE32 (`0x10B`) |
| --- | --- | --- |
| `Characteristics` (`IMAGE_FILE_DLL = 0x2000`) | `pe + 0x16` | `pe + 0x16` |
| `OptionalHeader.Magic` | `pe + 0x18` | `pe + 0x18` |
| `AddressOfEntryPoint` | `pe + 0x28` | `pe + 0x28` |
| `SizeOfImage` | `pe + 0x50` | `pe + 0x50` |
| `DllCharacteristics` | `pe + 0x5E` | `pe + 0x5E` |
| 데이터 디렉터리 배열 시작 | `pe + 0x88` (`136`) | `pe + 0x78` (`120`) |
| 익스포트 디렉터리 (`DD[0]`) | `pe + 0x88` | `pe + 0x78` |
| 임포트 디렉터리 (`DD[1]`) | `pe + 0x90` | `pe + 0x80` |
| 리소스 디렉터리 (`DD[2]`) | `pe + 0x98` | `pe + 0x88` |
| 베이스 재배치 (`DD[5]`) | `pe + 0xB0` | `pe + 0xA0` |
| TLS 디렉터리 (`DD[9]`) | `pe + 0xD0` | `pe + 0xC0` |
| IAT (`DD[12]`) | `pe + 0xE8` | `pe + 0xD8` |
| CLR / COM 디스크립터 (`DD[14]`) | `pe + 0xF8` | `pe + 0xE8` |

## 빌드별 `AL` 바이트코드 옵코드

| 바이트 | 명령어 | 디코딩된 연산 |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | 건너뜀 |
| `C0 C0 ib` | `ROL AL, imm8` | `("rol", imm)` |
| `C0 C8 ib` | `ROR AL, imm8` | `("ror", imm)` |
| `FE C0` | `INC AL` | `("inc",)` |
| `FE C8` | `DEC AL` | `("dec",)` |
| `C3` | `RET` | 스텁 종료 |

## 검증 스위트

위의 모든 변환 연산은 [검증 및 레퍼런스](https://app.gitbook.com/s/B5aYhrgw97Xp8Yd3YI4L/)에 수록된 25개 기준 테스트 항목을 대상으로 독립적인 Rust 구현체와 총 31회 비교하여 교차 검증합니다. 저장소 루트에서 `python verification/run_tests.py`와 `python verification/verify_docs.py`를 실행하면 모든 구현체와 문서 내 코드 블록을 다시 검증할 수 있습니다.
