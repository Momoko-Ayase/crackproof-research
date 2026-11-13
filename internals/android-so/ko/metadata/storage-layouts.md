---
description: "외부 global-metadata.dat 앱 페어링 및 내장 XOR 마스킹 슬림 v24 블롭"
icon: table
---

# 저장 레이아웃

보호가 적용된 Android IL2CPP 빌드는 다음 두 가지 저장 형태 중 하나로 메타데이터를 배포합니다.

| 형태 | 위치 | 복원 후 헤더 포맷 |
| --- | --- | --- |
| 외부 `global-metadata.dat` | `assets/bin/Data/Managed/Metadata/`(또는 분할 에셋 APK) 하위의 독립 파일 | 버전 `24`(`v24.1`), `29`, `31`, `39`의 표준 `0xFAB11BAF` 헤더 |
| 내장 슬림 + XOR 블롭 | 복원된 `libil2cpp.so` 이미지 내부의 `0x2701F30`바이트 데이터 블롭 | 프로브용 초기 두 dword `[0x9732CA38, 0xBAC4374F]`를 `[0xFAB11BAF, 24]`로 다시 기록 |

{% hint style="info" %}
Stage 2의 `0x5C` 레코드 디스크립터 안에 있는 `metadata_offset` / `metadata_size` 필드는 프로텍터 모듈 자체의 로드, 재배치, 임포트 메타데이터를 담으며, IL2CPP의 `global-metadata.dat` 파일과는 무관합니다. 외부 `v24.1` `global-metadata.dat` 파일을 모듈 `0x0C`와 짝지을 때는 두 파일이 동일한 애플리케이션 패키지에 속해야 합니다(분할 APK 간 `AndroidManifest.xml`의 `package` 및 `versionCode`/`versionCodeMajor`가 일치하거나, 동일한 `<root>/lib/<abi>/` 및 `<root>/assets/` 디렉터리 트리를 공유해야 함).
{% endhint %}

## 내장 슬림 + XOR 형태

초기 버전 `24` 빌드 일부는 `assets/`에 별도의 `global-metadata.dat` 파일을 두지 않고, 복원된 `.so` 데이터 섹션 내부에 `0x2701F30`바이트 크기의 XOR 마스킹 블롭을 내장합니다.

* **구조:** `0x100`바이트 헤더(리틀 엔디언 `u32` 워드 64개, 헤더 워드마다 개별 32비트 XOR 키 1개 적용) 뒤에 길이가 불규칙한 본문 세그먼트 256개(세그먼트마다 고유한 32비트 XOR 키 하나를 내부 dword 전체에 적용)가 이어집니다.
* **헤더 프로브 및 보정:** 첫 두 dword를 `[0x39184C70, 0xD901AFD4]`와 XOR하면 바이트 순서가 뒤바뀐 센티널 쌍 `[0x9732CA38, 0xBAC4374F]`가 나타납니다. 64개의 헤더 키와 256개의 세그먼트 키를 적용한 뒤 이 첫 두 dword를 `[0xFAB11BAF, 24]`로 고쳐 쓰면 유효한 슬림 버전 24 메타데이터 파일이 만들어집니다.
* **키 유도 현황:** 런타임에는 메타데이터 로더가 이 320개의 `u32` 내장 키스트림을 동적으로 생성하며, `.so` 바이너리만으로 해당 키스트림을 정적으로 유도하는 방법은 아직 규명되지 않았습니다. 같은 계열의 후속 빌드는 시드 기반 `MethodDef` 순열을 사용하는 외부 `global-metadata.dat` 파일 방식으로 전환되었습니다.
