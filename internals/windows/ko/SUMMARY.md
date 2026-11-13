# Table of contents

* [CrackProof for Windows 내부 구조](README.md)

## 파일 구조 <a href="#file-structure" id="file-structure"></a>

* [개요](file-structure/file-format.md)
* [컨테이너와 암호화 헤더](file-structure/container-layout.md)
* [식별 및 빌드 패밀리](file-structure/recognition.md)
* [섹션 데이터와 컴패니언 파일](file-structure/companion-layout.md)

## 데이터 변환 <a href="#data-transforms" id="data-transforms"></a>

* [개요](data-transforms/data-transforms.md)
* [롤링 키 및 회전 암호](data-transforms/rolling-and-rotation.md)
* [LFSR, 문자열 및 페이지 변환](data-transforms/lfsr-strings-pages.md)
* [체크섬과 키 진행](data-transforms/checksums.md)
* [AES-CBC 계층](data-transforms/aes.md)
* [Huffman 및 LZ 압축](data-transforms/compression.md)
* [빌드별 바이트 변환](data-transforms/bytecode-transform.md)

## 로딩 및 PE 복구 <a href="#loading-and-pe-repair" id="loading-and-pe-repair"></a>

* [로딩 및 섹션 복원](loading-and-pe-repair/loading/README.md)
  * [스테이지 체인과 마커 레이아웃](loading-and-pe-repair/loading/stage-chain.md)
  * [PE32, DLL 및 마커 없는 레이아웃](loading-and-pe-repair/loading/layout-variants.md)
  * [구조 탐색 및 검증](loading-and-pe-repair/loading/discovery-validation.md)
* [PE 재구성](loading-and-pe-repair/pe-reconstruction/README.md)
  * [헤더, 섹션 및 0 채우기 범위](loading-and-pe-repair/pe-reconstruction/memory-image.md)
  * [임포트, TLS 및 익스포트](loading-and-pe-repair/pe-reconstruction/imports-tls-exports.md)
  * [재배치, 페이지 변환 및 CLR 데이터](loading-and-pe-repair/pe-reconstruction/relocations-managed.md)

## 런타임 <a href="#runtime" id="runtime"></a>

* [개요](runtime/runtime.md)
* [부트 시퀀스와 상태 코드](runtime/startup-status.md)
* [환경 및 분석 방지 검사](runtime/environment-checks.md)
* [페이지 보호와 로더 코드](runtime/page-protection.md)
* [수동 매핑 보조 모듈](runtime/mapped-modules.md)
* [Htsysm 커널 컴포넌트](runtime/kernel-components.md)

## 분석 <a href="#analysis" id="analysis"></a>

* [개요](analysis/analysis.md)
* [분석 워크플로](analysis/workflow.md)
* [확인된 한계점](analysis/observed-limitations.md)
* [il2cpp 메타데이터 난독화](analysis/il2cpp-metadata.md)
* [상수 및 오프셋](analysis/constants.md)
