---
description: "가역 암호, 체크섬, AES 스케줄, Huffman/LZ 압축 및 바이트코드 VM 개요"
icon: shuffle
---

# 데이터 변환

CrackProof는 헤더, 스테이지 디스크립터, 임포트 문자열, 섹션 페이로드, 실행 코드 페이지 전반에 걸쳐 바이트/dword 단위 암호, CRC-32 키 파생, AES-CBC, Huffman/LZ 압축, 빌드별 바이트코드 치환을 다층으로 적용합니다. 이 섹션의 각 문서는 정확한 비트 단위 연산을 실행 가능한 Python 레퍼런스 코드와 함께 설명합니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-rotate"></i></td><td><strong>롤링 키 및 회전 암호</strong></td><td><code>payload_xor_chain</code>, <code>xor_ror_dwords</code>, 디스크립터/주소 기반 3중 바이트 회전 암호.</td><td><a href="rolling-and-rotation.md">롤링 키 및 회전 암호</a></td></tr><tr><td><i class="fa-wave-square"></i></td><td><strong>LFSR, 문자열 및 페이지 변환</strong></td><td><code>0x8003</code> LFSR 스텁 암호, RVA 기반 임포트 이름 문자열 암호, 페이지 단위 <code>.text</code> 스크램블.</td><td><a href="lfsr-strings-pages.md">LFSR, 문자열 및 페이지 변환</a></td></tr><tr><td><i class="fa-hashtag"></i></td><td><strong>체크섬 및 키 진행</strong></td><td>반전(reflected) CRC-32, 회전 워드 체크섬, 삼각수 기반 다중 라운드 키 진행.</td><td><a href="checksums.md">체크섬 및 키 진행</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>AES-CBC 계층</strong></td><td>제로 IV 기반 AES-CBC 복호화, 버퍼 내장형 키 스케줄, 회전된 최종 라운드 S-box 테이블.</td><td><a href="aes.md">AES-CBC 계층</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>Huffman 및 LZ 압축</strong></td><td>3바이트 Huffman 트리 엔트리와 리터럴, 누산기, 런 채우기(run-fill), LZ 토큰의 네 가지 모드.</td><td><a href="compression.md">Huffman 및 LZ 압축</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>빌드별 바이트 변환</strong></td><td>섹션 페이로드용 9-옵코드 <code>AL</code> x86 바이트코드 인터프리터와 256바이트 역변환 룩업 테이블.</td><td><a href="bytecode-transform.md">빌드별 바이트 변환</a></td></tr></tbody></table>
