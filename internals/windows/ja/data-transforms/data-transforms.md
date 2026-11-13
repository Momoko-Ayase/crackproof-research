---
description: "Windows 版で使われる可逆暗号、チェックサム、AES、圧縮、バイトコード変換の概要。"
icon: shuffle
---

# データ変換

CrackProof は、ヘッダー、ステージディスクリプター、インポート文字列、セクションペイロード、および実行可能コードページにわたって、バイト／dword 単位の暗号、CRC-32 による鍵導出、AES-CBC、Huffman/LZ 圧縮、ビルドごとのバイトコード置換を多層的に組み合わせています。以下の各ページでは、それぞれのビットレベル演算を実行可能な Python リファレンスコードとともに解説します。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-rotate"></i></td><td><strong>ローリング鍵暗号とローテーション暗号</strong></td><td><code>payload_xor_chain</code>、<code>xor_ror_dwords</code>、およびディスクリプター／アドレスを鍵とする 3 段バイトローテーション暗号。</td><td><a href="rolling-and-rotation.md">ローリング鍵暗号とローテーション暗号</a></td></tr><tr><td><i class="fa-wave-square"></i></td><td><strong>LFSR・文字列・ページ変換</strong></td><td><code>0x8003</code> LFSR スタブ暗号、RVA を鍵とするインポート名文字列暗号、ページ単位の <code>.text</code> スクランブル。</td><td><a href="lfsr-strings-pages.md">LFSR・文字列・ページ変換</a></td></tr><tr><td><i class="fa-hashtag"></i></td><td><strong>チェックサムと鍵更新</strong></td><td>ビット反転型 CRC-32、ローテーション付きワードチェックサム、三角数による多段鍵更新。</td><td><a href="checksums.md">チェックサムと鍵更新</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>AES-CBC レイヤー</strong></td><td>バッファー内鍵スケジュールとローテーション済み最終ラウンド S-box テーブルを用いたゼロ IV の AES-CBC 復号。</td><td><a href="aes.md">AES-CBC レイヤー</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>Huffman・LZ 圧縮</strong></td><td>3 バイト形式の Huffman 木エントリと、リテラル・アキュムレーター・ランレングス充填・LZ の 4 トークンモード。</td><td><a href="compression.md">Huffman・LZ 圧縮</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>ビルド固有のバイト変換</strong></td><td>セクションペイロードに適用される 9 オペコード構成の <code>AL</code> x86 バイトコードインタープリターと 256 バイト逆変換テーブル。</td><td><a href="bytecode-transform.md">ビルド固有のバイト変換</a></td></tr></tbody></table>
