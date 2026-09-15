---
description: 文档中 Python 片段的可运行验证套件，以及从真实受保护二进制捕获的脱敏参考材料。
---

# 验证与参考

本栏目以完整、可运行的形式发布 [CrackProof 内部机制](https://app.gitbook.com/o/-Lx9XUuXVg8x3nx7ouIX/s/fEb9nKPvKsjkPAHMUbOt/)背后的参考材料。

## 验证套件

主文档中的每个 Python 片段在发布前都经过验证：每个函数的输出在相同输入上与算法的独立参考移植逐字节比对。完整套件——每个文件一页：

| 文件                | 作用                                               |
| ----------------- | ------------------------------------------------ |
| `primitives.py`   | 滚动密钥密码、字节旋转、LFSR、字符串密码、页置乱、按需页密码、CRC-32、校验和、三角调度 |
| `aes_impl.py`     | 带缓冲区内置密钥调度的 AES-CBC 解密                           |
| `huffman.py`      | Huffman/LZ 混合解压器                                 |
| `bytecode_vm.py`  | 逐构建字节码桩解码器/解释器及其逆变换                              |
| `detect.py`       | 基于内容的识别与分类                                       |
| `run_tests.py`    | 比对工具（32 个向量）                                     |
| `rust_vectors.rs` | 打印基准真值的独立参考移植                                    |
| `vectors.txt`     | 比对工具所对照的期望输出                                     |

要重跑全部比对，下载这些文件并执行 `python run_tests.py`。预期结果：`all vectors match`。

## 参考捕获

调试日志示例——从受保护进程捕获的真实 CrackProof 调试日志，已脱敏：一个功能完整的宿主 EXE（页加密）、一个原生插件 DLL（仅整体解密）与一个托管 DLL。
