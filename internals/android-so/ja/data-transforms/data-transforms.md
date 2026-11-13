---
description: "GF(2^32) 演算、モジュールシード、AES 鍵、コンテナー復号、Huffman/LZ 圧縮"
icon: shuffle
---

# データ変換

復号処理は 4 つの層で構成されています。Stage 1 の 32 ビットワード暗号、Stage 2 の GF(2³²) 攪拌を用いたストリームヘッダーおよびレコード記述子の復号、コンテナー内のセグメント単位ローリングワード暗号と省略可能な AES-256-CBC 復号、そして Huffman/LZ 展開です。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-rotate"></i></td><td><strong>ワード・ストリーム・レコード暗号</strong></td><td>GF(2³²) 固定乗算、Stage 1 ワード暗号、ストリームヘッダー、<code>0x5C</code> レコード記述子、および <code>0x9D</code> 保護記述子。</td><td><a href="word-and-record.md">ワード・ストリーム・レコード暗号</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>モジュール設定</strong></td><td>鍵スケジュールマーカー <code>00 01 0e 00</code>、AES-256 鍵の復元、モジュール <code>0x9B</code> と埋め込み Stage 2 のシード配置。</td><td><a href="module-config.md">モジュール設定</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>コンテナー変換</strong></td><td>コンテナーヘッダー、セグメントローリング暗号、ファイルレイアウト writer、および補助 ELF コンテナー。</td><td><a href="container.md">コンテナー変換</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>Huffman / LZ 圧縮</strong></td><td>3 バイト要素の Huffman 森、16 ビットプレフィックステーブル、4 種のトークンモード、および消費ビット・バイト長の一致検証。</td><td><a href="compression.md">Huffman / LZ 圧縮</a></td></tr></tbody></table>
