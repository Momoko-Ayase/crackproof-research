---
description: 文檔中 Python 片段的可運行驗證套件，以及從真實受保護二進制捕獲的脫敏參考材料。
---

# 驗證與參考

本欄目以完整、可運行的形式發佈 [CrackProof 內部機制](https://app.gitbook.com/o/-Lx9XUuXVg8x3nx7ouIX/s/sFi4W2Zr1UBoxZd5YI3A/)背後的參考材料。

## 驗證套件

主文檔中的每個 Python 片段在發佈前都經過驗證：每個函數的輸出在相同輸入上與算法的獨立參考移植逐字節比對。完整套件——每個文件一頁：

| 文件                | 作用                                               |
| ----------------- | ------------------------------------------------ |
| `primitives.py`   | 滾動密鑰密碼、字節旋轉、LFSR、字符串密碼、頁置亂、按需頁密碼、CRC-32、校驗和、三角調度 |
| `aes_impl.py`     | 帶緩衝區內置密鑰調度的 AES-CBC 解密                           |
| `huffman.py`      | Huffman/LZ 混合解壓器                                 |
| `bytecode_vm.py`  | 逐構建字節碼樁解碼器/解釋器及其逆變換                              |
| `detect.py`       | 基於內容的識別與分類                                       |
| `run_tests.py`    | 比對工具（32 個向量）                                     |
| `rust_vectors.rs` | 打印基準真值的獨立參考移植                                    |
| `vectors.txt`     | 比對工具所對照的期望輸出                                     |

要重跑全部比對，下載這些文件並執行 `python run_tests.py`。預期結果：`all vectors match`。

## 參考捕獲

調試日誌示例——從受保護進程捕獲的真實 CrackProof 調試日誌，已脫敏：一個功能完整的宿主 EXE（頁加密）、一個原生插件 DLL（僅整體解密）與一個託管 DLL。
