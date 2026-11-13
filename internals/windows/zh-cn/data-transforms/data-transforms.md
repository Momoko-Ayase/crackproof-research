---
description: "Windows 端可逆密码、校验和、AES 轮密钥表、Huffman/LZ 与字节码变换总览。"
icon: shuffle
---

# 数据变换

CrackProof 在头部、阶段描述符、导入表字符串、节数据载荷与可执行代码页上叠加了多层字节/双字加解密变换、CRC-32 密钥派生、AES-CBC、Huffman/LZ 压缩以及按构建生成的字节码置换。本节各页给出具体的位运算定义与可直接运行的 Python 参考实现。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-rotate"></i></td><td><strong>滚动密钥与循环移位算法</strong></td><td><code>payload_xor_chain</code>、<code>xor_ror_dwords</code> 以及按描述符或地址派生的三重字节循环移位算法。</td><td><a href="rolling-and-rotation.md">滚动密钥与循环移位算法</a></td></tr><tr><td><i class="fa-wave-square"></i></td><td><strong>LFSR、字符串与代码页变换</strong></td><td><code>0x8003</code> LFSR 字节码存根解密、按 RVA 派生密钥的导入名字符串解密，以及 <code>.text</code> 逐页代码混淆。</td><td><a href="lfsr-strings-pages.md">LFSR、字符串与代码页变换</a></td></tr><tr><td><i class="fa-hashtag"></i></td><td><strong>校验和与密钥步进</strong></td><td>反射 CRC-32、带长度异或的区域校验和，以及三角和式多轮密钥步进。</td><td><a href="checksums.md">校验和与密钥步进</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>AES-CBC 解密层</strong></td><td>使用映像缓冲区内嵌轮密钥表与末轮旋转逆 S-box 表的零 IV AES-CBC 解密。</td><td><a href="aes.md">AES-CBC 解密层</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>Huffman 与 LZ 压缩</strong></td><td>3 字节 Huffman 树节点表，以及字面量、计数累加、游程填充与 LZ 回溯四种令牌模式。</td><td><a href="compression.md">Huffman 与 LZ 压缩</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>按构建生成的字节变换</strong></td><td>操作 <code>AL</code> 的九操作码 x86 字节码解释器，以及用于节载荷还原的 256 字节逆变换查找表。</td><td><a href="bytecode-transform.md">按构建生成的字节变换</a></td></tr></tbody></table>
