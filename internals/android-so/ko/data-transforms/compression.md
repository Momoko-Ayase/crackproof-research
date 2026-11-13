---
description: "3바이트 Huffman 포레스트, 16비트 프리픽스 테이블 및 4가지 LZ/반복 토큰 모드"
icon: file-zipper
---

# Huffman 및 LZ 압축

압축된 컨테이너 블록은 [Windows Huffman/LZ 포맷](https://app.gitbook.com/s/FlY9nVrA6FxLQBrkLIc2/data-transforms/compression)과 동일한 3바이트 Huffman 트리 엔트리 및 4모드 토큰 인코딩을 사용합니다. 테이블의 각 노드는 3바이트(`u16 value`, `u8 bit_len`)로 구성됩니다. 8비트 조회 테이블로 초기 루트 노드를 선택하고 16비트 프리픽스 테이블로 짧은 코드를 빠르게 디코딩하며, 더 긴 코드는 리프 노드(`value & 0x8000 != 0`)에 도달할 때까지 입력 비트를 1비트씩 읽으며 형제 노드 쌍(`value`와 `value + 1`)을 따라 내려갑니다.

## 토큰 모드

리프 값의 비트 15를 지우면 10비트 심볼이 남으며, 비트 `8..9`가 모드를 선택하고 비트 `0..7`이 `payload`를 담습니다. 16비트 누산기 `pending`은 `0`에서 시작합니다.

| 모드 (`sym & 0x300`) | 페이로드 (`sym & 0xFF`) | 동작 |
| --- | --- | --- |
| `0x000` | 리터럴 바이트 | `payload` 1바이트를 그대로 출력 (`pending`은 반드시 `0`이어야 함) |
| `0x100` | 카운트 바이트 | `pending > 0xFF`이면 거부하고, 그렇지 않으면 아무 바이트도 출력하지 않은 채 `pending = (pending << 8) \| payload` 설정 |
| `0x200` | 단위 폭 (`1`, `2`, `4`) | `reps = max(pending, 1)`로 두고 직전에 기록된 `payload`바이트 단위를 `reps`회 반복 출력(총 `reps * payload`바이트)한 뒤 `pending = 0`으로 초기화 |
| `0x300` | 일치 길이 (`length`) | 출력 버퍼의 `output_pos - distance` 위치(`distance = pending + length`)에서 `length`바이트를 복사한 뒤 `pending = 0`으로 초기화 |

<details>
<summary>토큰 디코딩 예시</summary>

출력 버퍼 끝에 4바이트 리틀 엔디안 워드 `11 22 33 44`가 기록되어 있고 `output_pos = 4`인 상태라고 가정합니다.

1. 리프 `0x8103` (`mode = 0x100`, `payload = 0x03`): `pending`이 `0x0003`이 되며, 바이트는 출력하지 않습니다.
2. 리프 `0x8204` (`mode = 0x200`, `payload = 4`): 단위 폭이 `4`바이트이고 `reps = 3`이므로 `11 22 33 44`를 3회 반복하여 기록하고(`12`바이트 출력, `output_pos = 16`), `pending`을 `0`으로 초기화합니다.
3. 리프 `0x8104` (`mode = 0x100`, `payload = 0x04`) 뒤에 `0x8306` (`mode = 0x300`, `payload = 6`)이 이어짐: `length = 6`, `distance = 4 + 6 = 10`이 되어 `output[6..12]`(`output_pos - distance = 6`)에서 6바이트를 복사하고 `pending`을 `0`으로 초기화합니다.
</details>

## 검증 불변식

* **반복 채우기 (`0x200`):** `payload`는 반드시 `1`, `2`, `4` 중 하나여야 하며, 출력 버퍼에 이미 최소 `payload`바이트가 존재해야 하고 `output_pos + max(pending, 1) * payload`가 `out_len`을 초과해서는 안 됩니다.
* **역참조 복사 (`0x300`):** `distance = pending + length`는 `distance <= output_pos` 및 `output_pos + length <= out_len`을 만족해야 합니다(`distance < length`일 때 바이트 단위로 겹쳐서 순방향 복사하는 동작은 유효함).
* **정확한 종료 조건:** 압축 해제는 `output_pos == out_len`, `pending == 0`, `div_ceil(consumed_bits, 8) == src_len`이 모두 성립할 때만 성공으로 처리됩니다. 범위를 벗어난 노드 인덱스, 비트 길이가 0인 리프, `pending` 오버플로, 읽히지 않고 남은 후미 바이트가 하나라도 있으면 컨테이너 디코딩은 실패합니다.
