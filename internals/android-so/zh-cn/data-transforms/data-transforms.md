---
description: "Android 流中的 GF(2^32) 算术、模块种子、AES 轮密钥、容器解码与压缩。"
icon: shuffle
---

# 数据变换

解密过程依次经过四层变换：第一阶段的 32 位按字解密、第二阶段基于 GF(2³²) 混淆的流头与记录描述符解密、容器内按段执行的滚动字解密及可选 AES-256-CBC 解密，以及最内层的 Huffman/LZ 解压缩。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-rotate"></i></td><td><strong>字、流与记录加解密</strong></td><td>GF(2³²) 定值乘法、第一阶段按字解密、流头、<code>0x5C</code> 记录描述符与 <code>0x9D</code> 加密描述符。</td><td><a href="word-and-record.md">字、流与记录加解密</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>模块配置</strong></td><td>轮密钥表标记 <code>00 01 0e 00</code>、AES-256 密钥恢复，以及模块 <code>0x9B</code> 与内置第二阶段解码器的种子布局差异。</td><td><a href="module-config.md">模块配置</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>容器变换</strong></td><td>容器头、按段滚动解密、文件布局写入表，以及辅助 ELF 容器。</td><td><a href="container.md">容器变换</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>Huffman 与 LZ 压缩</strong></td><td>3 字节结点 Huffman 表、16 位前缀加速表、四种符号模式与精确位/字节消耗校验。</td><td><a href="compression.md">Huffman 与 LZ 压缩</a></td></tr></tbody></table>
