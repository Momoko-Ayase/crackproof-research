---
description: "GF(2³²) 암호, 모듈 설정, 컨테이너 디코더 및 Huffman/LZ 압축 계층"
icon: shuffle
---

# 데이터 변환

복호화는 네 계층을 순서대로 거칩니다. Stage 1의 32비트 워드 암호에서 시작해 Stage 2의 GF(2³²) 믹싱 기반 스트림 헤더와 레코드 디스크립터, 컨테이너 내부의 세그먼트별 롤링 워드 암호와 선택적 AES-256-CBC 복호화를 거쳐 Huffman/LZ 압축 해제로 이어집니다.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-rotate"></i></td><td><strong>워드, 스트림 및 레코드 암호</strong></td><td>GF(2³²) 고정 곱셈, Stage 1 워드 암호, 스트림 헤더, <code>0x5C</code> 레코드 디스크립터, <code>0x9D</code> 보호 디스크립터를 다룹니다.</td><td><a href="word-and-record.md">워드, 스트림 및 레코드 암호</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>모듈 설정</strong></td><td>키 스케줄 마커 <code>00 01 0e 00</code>, AES-256 키 복원, 모듈 <code>0x9B</code>와 내장 Stage 2 디코더의 시드 레이아웃을 다룹니다.</td><td><a href="module-config.md">모듈 설정</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>컨테이너 변환</strong></td><td>컨테이너 헤더, 세그먼트 롤링 암호, 파일 레이아웃 라이터, 보조 ELF 재배치 컨테이너를 다룹니다.</td><td><a href="container.md">컨테이너 변환</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>Huffman 및 LZ 압축</strong></td><td>3바이트 Huffman 포레스트, 16비트 프리픽스 테이블, 4가지 토큰 모드, 입력 비트 및 바이트 소비 검증을 다룹니다.</td><td><a href="compression.md">Huffman 및 LZ 압축</a></td></tr></tbody></table>
