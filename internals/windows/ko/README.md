---
description: "CrackProof Windows PE의 파일 구조, 데이터 변환, 복원 및 런타임 동작"
icon: desktop
---

# CrackProof for Windows 내부 구조

CrackProof for Windows는 PE32 (`0x10B`) 및 PE32+ (`0x20B`) 실행 파일과 DLL을 보호합니다. 보호된 바이너리는 부트스트랩 로더를 매핑하는 유효한 외부 PE 셸을 유지하며, 원본 애플리케이션 섹션, 로더 스테이지, 임포트 및 CLR 메타데이터, 코드 페이지는 암호화 및 압축된 형태로 저장합니다. 로드 시점에 런타임은 호스트 환경을 검사해 메모리 이미지를 재구성하고, 설정에 따라 폴트 핸들러 기반 실행 페이지 보호를 활성화한 뒤 원본 엔트리 포인트(OEP)로 제어를 넘깁니다.

확인된 빌드는 네이티브 및 관리형(.NET) EXE와 DLL, 마커 기반 및 마커 없는(marker-less) 64비트 셸, 표준형 및 컴팩트 32비트 셸, 전용 64비트 DLL 컨테이너, 그리고 4 KiB 스텁과 외부 `._` 컴패니언 파일로 분할된 PE32+ 모듈을 포괄합니다.

## 표기 규칙

* 별도 언급이 없는 한 모든 오프셋은 파일 시작 지점 기준의 16진수 바이트 오프셋입니다. `u32@X`는 오프셋 `X`에 위치한 리틀 엔디언 32비트 부호 없는 정수를 뜻합니다.
* **RVA**(상대 가상 주소)는 표준 PE 규약을 따릅니다. 이미지 복원은 RVA로 인덱싱한 이미지 버퍼에서 수행합니다(64비트 출력은 `VirtualAddress == PointerToRawData`를 유지하며, 32비트 출력은 파일 정렬 단위인 `0x200`에 맞춰 섹션을 재정렬합니다).
* 정수 연산은 x86 명령어 의미론과 동일한 고정 폭 8비트 또는 32비트 부호 없는 래핑(wraparound) 연산을 사용하며, Python 코드 조각에서는 비트마스크(`& 0xFF`, `& 0xFFFFFFFF`)를 명시적으로 적용합니다.
* `info[0..7]`은 파일 오프셋 `0x1000`에서 복호화된 8개의 32비트 워드를 가리킵니다([컨테이너 및 암호화된 헤더](file-structure/container-layout.md) 참고).

## 구성 섹션

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-folder-tree"></i></td><td><strong>파일 구조</strong></td><td><code>0x1000</code> 기준의 디스크 컨테이너 분할, <code>KONN</code> 헤더 KDF, 빌드 계열, 외부 <code>._</code> 컴패니언 파일.</td><td><a href="file-structure/file-format.md">보호된 파일 구조</a></td></tr><tr><td><i class="fa-shuffle"></i></td><td><strong>데이터 변환</strong></td><td>롤링 XOR 및 회전 암호, LFSR, 문자열 및 페이지 스크램블, CRC/스테이지 키, AES-CBC, Huffman/LZ 압축, 바이트코드 VM.</td><td><a href="data-transforms/data-transforms.md">데이터 변환</a></td></tr><tr><td><i class="fa-stairs"></i></td><td><strong>로딩 및 섹션 복구</strong></td><td>9단계 64비트 스테이지 체인, PE32 표준형/컴팩트 및 전용 DLL 변형, 마커 없는 구조 탐색.</td><td><a href="loading-and-pe-repair/loading/README.md">로딩 및 섹션 복구</a></td></tr><tr><td><i class="fa-puzzle-piece"></i></td><td><strong>PE 재구성</strong></td><td>섹션 헤더, 임시 EP/디렉터리 블록, 임포트 테이블과 <code>.kmiat</code>, TLS, 익스포트 테이블, 재배치, CLR 오버레이.</td><td><a href="loading-and-pe-repair/pe-reconstruction/README.md">PE 재구성</a></td></tr><tr><td><i class="fa-play"></i></td><td><strong>런타임</strong></td><td>상태 로깅, <code>AAA-BBB-CCC</code> 오류 코드, 분석 방지 검사, <code>KiUserExceptionDispatcher</code> 페이지 보호, 헬퍼 및 <code>Htsysm</code> 드라이버.</td><td><a href="runtime/runtime.md">런타임 동작</a></td></tr><tr><td><i class="fa-compass"></i></td><td><strong>분석 노트</strong></td><td>정적/런타임 분석 절차, 확인된 한계점, <code>-GMD</code> IL2CPP 메타데이터 재매핑, 전체 오프셋/상수 참조표.</td><td><a href="analysis/analysis.md">분석 노트</a></td></tr></tbody></table>

이 섹션에서 다루는 변환 알고리즘의 실행 가능한 Python 레퍼런스 구현과 테스트 벡터는 [검증 및 레퍼런스](https://app.gitbook.com/s/XSPACE_REFERENCE_KO/)에 수록되어 있습니다. 3바이트 Huffman/LZ 토큰 인코딩과 버퍼 내장형 AES 키 스케줄은 [CrackProof for Android SO 내부 구조](https://app.gitbook.com/s/XSPACE_ANDROID_KO/)에서도 동일하게 사용됩니다.
