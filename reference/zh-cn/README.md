---
description: "可运行的 Windows 片段检查与脱敏参考捕获。"
---

# 验证与参考

本栏目完整、可运行地发布 [CrackProof 内部机制](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/)所用的参考材料。

## 验证套件

两项检查覆盖 [CrackProof Windows 内部机制](https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/) 中的 Python 示例。`run_tests.py` 对参考实现文件运行 31 项比对。`verify_docs.py` 在每种语言的九个 Windows 页面中执行全部 16 个 Python 代码块，每种语言运行 27 项比对。检查使用固定参考向量与已知答案，不能证明所有输入或运行时行为。套件按每个文件一页发布：

| 文件                | 作用                                               |
| ----------------- | ------------------------------------------------ |
| `primitives.py`   | 滚动密钥密码、字节旋转、LFSR、字符串密码、页置乱、按需页密码、CRC-32、校验和、三角调度 |
| `aes_impl.py`     | 带缓冲区内置密钥调度的 AES-CBC 解密                           |
| `huffman.py`      | Huffman/LZ 混合解压器                                 |
| `bytecode_vm.py`  | 逐构建字节码桩解码器/解释器及其逆变换                              |
| `detect.py`       | 基于内容的识别与分类                                       |
| `run_tests.py`    | 参考实现比对工具（31 项比对） |
| `verify_docs.py`  | Markdown 检查器（三种语言，共 81 项比对） |
| `rust_vectors.rs` | 打印参考输出的独立移植 |
| `vectors.txt`     | 检查使用的 25 条具名参考记录 |

把参考 Python 文件与 `vectors.txt` 放在一起，然后运行 `python run_tests.py`。脚本会查找自身旁边的向量文件。预期结果：`all vectors match`。

在文档仓库根目录运行：

```bash
python verification/run_tests.py
python verification/verify_docs.py
```

Markdown 检查器需要文档目录树，结束时输出 `all Windows doc snippets verified (3 languages, 48 Python blocks, 81 checks)`。这些检查覆盖 Windows Python 示例；Android 伪代码与非 Python 示例需要另行验证。

## 参考捕获

[调试日志示例](sample-debug-logs.md) 页发布从受保护进程捕获并脱敏的真实 CrackProof 调试日志：一个功能完整的宿主 EXE（页加密）、一个原生插件 DLL（仅整体解密）与一个托管 DLL。
