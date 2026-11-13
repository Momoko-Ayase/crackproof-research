# Table of contents

* [CrackProof for Android SO 내부 구조](README.md)

## 파일 형식 <a href="#file-format" id="file-format"></a>

* [개요](file-format/file-format.md)
* [보호된 ELF](file-format/protected-elf.md)
* [1단계 헤더](file-format/stage1.md)
* [2단계 스트림](file-format/stage2-streams.md)

## 데이터 변환 <a href="#data-transforms" id="data-transforms"></a>

* [개요](data-transforms/data-transforms.md)
* [워드, 스트림 및 레코드 암호](data-transforms/word-and-record.md)
* [모듈 설정](data-transforms/module-config.md)
* [컨테이너 변환](data-transforms/container.md)
* [Huffman 및 LZ 압축](data-transforms/compression.md)

## 복원 <a href="#restoration" id="restoration"></a>

* [개요](restoration/restoration.md)
* [모듈 스트림](restoration/module-streams.md)
* [동적 링킹](restoration/dynamic-linking.md)
* [ELF 출력](restoration/elf-output.md)

## 런타임 <a href="#runtime" id="runtime"></a>

* [개요](runtime/runtime.md)
* [1단계 부트스트랩](runtime/stage1-bootstrap.md)
* [2단계 인터프리터](runtime/stage2-interpreter.md)
* [환경 및 무결성 검사](runtime/environment-checks.md)
* [런타임 모듈](runtime/modules.md)

## 메타데이터 <a href="#metadata" id="metadata"></a>

* [개요](metadata/metadata.md)
* [메서드 토큰](metadata/method-tokens.md)
* [저장 레이아웃](metadata/storage-layouts.md)

## 분석 <a href="#analysis" id="analysis"></a>

* [개요](analysis/analysis.md)
* [검증 체크리스트](analysis/validation.md)
* [상수](analysis/constants.md)
