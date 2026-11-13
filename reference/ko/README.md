---
description: "실행 가능한 Python 레퍼런스 구현, 테스트 벡터, 스니펫 검증기 및 익명 디버그 로그."
icon: flask
---

# 검증 및 레퍼런스

이 섹션은 [CrackProof Windows 내부 구조](https://app.gitbook.com/s/FlY9nVrA6FxLQBrkLIc2/)의 기반이 되는 실행 가능한 전체 레퍼런스 코드와 테스트 벡터, 그리고 익명화된 런타임 디버그 로그를 수록합니다.

## 검증 스위트

이 저장소의 모든 Windows 변환 구현은 두 가지 자동 검사 스크립트로 검증합니다.

* **`run_tests.py` (비교 31건):** `verification/` 디렉터리의 독립 실행형 Python 모듈을 실행하여 `rust_vectors.rs`로 생성한 `vectors.txt`의 기준 레코드 25건과 대조합니다.
* **`verify_docs.py` (5개 언어, Python 블록 80개, 비교 135건):** 각 언어판(`en`, `zh-cn`, `zh-tw`, `ja`, `ko`)의 변환 문서 9개 페이지에서 Python 코드 블록 16개씩을 추출해 실행하며, 언어당 27건의 벡터 비교를 수행합니다.

```bash
python verification/run_tests.py
python verification/verify_docs.py
```

정상 실행 시 마지막 줄에 `all vectors match`와 `all Windows doc snippets verified (5 languages, 80 Python blocks, 135 checks)`가 출력됩니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-code"></i></td><td><strong>primitives.py</strong></td><td>롤링 XOR 체인, 비트 회전, LFSR, 문자열 암호, 페이지 스크램블, 온디맨드 페이지 복호화 암호, CRC-32 및 삼각 키 스케줄.</td><td><a href="primitives.py.md">primitives.py</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>aes_impl.py</strong></td><td>버퍼 내 키 스케줄과 GF(2⁸) 역 T-테이블을 사용하는 Zero-IV AES-CBC 복호화.</td><td><a href="aes_impl.py.md">aes_impl.py</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>huffman.py</strong></td><td>3바이트 Huffman 트리 디코더와 4모드 리터럴/런필(run-fill)/LZ 압축 해제기.</td><td><a href="huffman.py.md">huffman.py</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>bytecode_vm.py</strong></td><td>빌드별 9개 옵코드 <code>AL</code> x86 스텁 파서, 인터프리터, 256바이트 LUT 생성기 및 역변환기.</td><td><a href="bytecode_vm.py.md">bytecode_vm.py</a></td></tr><tr><td><i class="fa-fingerprint"></i></td><td><strong>detect.py</strong></td><td>콘텐츠 기반 <code>KONN</code> 헤더 KDF 식별 및 PE32/PE32+ 네이티브·관리형 분류기.</td><td><a href="detect.py.md">detect.py</a></td></tr><tr><td><i class="fa-circle-check"></i></td><td><strong>run_tests.py</strong></td><td><code>vectors.txt</code> 기준 31건의 비교를 수행하는 독립 테스트 러너.</td><td><a href="run_tests.py.md">run_tests.py</a></td></tr><tr><td><i class="fa-list-check"></i></td><td><strong>verify_docs.py</strong></td><td>5개 언어 Markdown 문서의 Python 코드 추출 및 검증기 (블록 80개, 검사 135건).</td><td><a href="verify_docs.py.md">verify_docs.py</a></td></tr><tr><td><i class="fa-gears"></i></td><td><strong>rust_vectors.rs</strong></td><td>기준 테스트 벡터인 <code>vectors.txt</code> 레코드를 생성하는 독립 Rust 포트.</td><td><a href="rust_vectors.rs.md">rust_vectors.rs</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>vectors.txt</strong></td><td>이름이 지정된 25개의 16진수 및 구조체 테스트 레코드.</td><td><a href="vectors.txt.md">vectors.txt</a></td></tr><tr><td><i class="fa-file-lines"></i></td><td><strong>샘플 디버그 로그</strong></td><td>페이지 암호화 호스트 EXE, 네이티브 플러그인 DLL, 관리형 DLL에서 수집한 익명화 런타임 트레이스.</td><td><a href="sample-debug-logs.md">샘플 디버그 로그</a></td></tr></tbody></table>
