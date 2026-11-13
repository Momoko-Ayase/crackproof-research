---
description: "可运行的 Python 参考实现、测试向量、文档代码校验器及脱敏 CrackProof 调试日志。"
icon: flask
---

# 验证与参考实现

本节提供与 [CrackProof Windows 内部机制](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/) 配套的完整可运行参考实现与测试向量，以及脱敏后的运行时调试日志。

## 验证套件

本仓库通过两项自动化检查校验全部 Windows 数据变换实现：

* **`run_tests.py`（31 项比对）：** 运行 `verification/` 下的独立 Python 模块，与 `vectors.txt` 中的 25 条基准记录（由 `rust_vectors.rs` 生成）逐一核对。
* **`verify_docs.py`（5 种语言、80 个 Python 代码块、135 项比对）：** 从五个语言版本（`en`、`zh-cn`、`zh-tw`、`ja`、`ko`）各自九篇数据变换文档中提取并执行全部 16 个 Python 代码块，每种语言执行 27 项测试向量比对。

```bash
python verification/run_tests.py
python verification/verify_docs.py
```

预期末尾输出为 `all vectors match` 与 `all Windows doc snippets verified (5 languages, 80 Python blocks, 135 checks)`。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-code"></i></td><td><strong>primitives.py</strong></td><td>滚动异或链、循环移位、LFSR、字符串密码、页面置乱、按需页面密码、CRC-32 与三角密钥编排。</td><td><a href="primitives.py.md">primitives.py</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>aes_impl.py</strong></td><td>采用缓冲区内密钥表与 GF(2⁸) 逆 T 表的零 IV AES-CBC 解密实现。</td><td><a href="aes_impl.py.md">aes_impl.py</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>huffman.py</strong></td><td>3 字节节点 Huffman 树解码器与四模式字面量/行程填充/LZ 解压实现。</td><td><a href="huffman.py.md">huffman.py</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>bytecode_vm.py</strong></td><td>按构建生成的九操作码 <code>AL</code> x86 存根解析器与解释器、256 字节 LUT 构造及逆置换。</td><td><a href="bytecode_vm.py.md">bytecode_vm.py</a></td></tr><tr><td><i class="fa-fingerprint"></i></td><td><strong>detect.py</strong></td><td>基于文件内容的 <code>KONN</code> 头部 KDF 识别与 PE32/PE32+ 原生/托管分类。</td><td><a href="detect.py.md">detect.py</a></td></tr><tr><td><i class="fa-circle-check"></i></td><td><strong>run_tests.py</strong></td><td>对照 <code>vectors.txt</code> 执行 31 项比对的独立测试脚本。</td><td><a href="run_tests.py.md">run_tests.py</a></td></tr><tr><td><i class="fa-list-check"></i></td><td><strong>verify_docs.py</strong></td><td>覆盖五种语言的 Markdown Python 代码块提取与校验脚本（80 个代码块，135 项检查）。</td><td><a href="verify_docs.py.md">verify_docs.py</a></td></tr><tr><td><i class="fa-gears"></i></td><td><strong>rust_vectors.rs</strong></td><td>用于生成 <code>vectors.txt</code> 基准记录的独立 Rust 移植实现。</td><td><a href="rust_vectors.rs.md">rust_vectors.rs</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>vectors.txt</strong></td><td>25 条具名十六进制与结构化测试向量记录。</td><td><a href="vectors.txt.md">vectors.txt</a></td></tr><tr><td><i class="fa-file-lines"></i></td><td><strong>调试日志示例</strong></td><td>采自页面加密宿主 EXE、原生插件 DLL 与托管 DLL 的脱敏运行时日志。</td><td><a href="sample-debug-logs.md">调试日志示例</a></td></tr></tbody></table>
