---
description: "可運行的 Windows 片段檢查與脫敏參考捕獲。"
---

# 驗證與參考

本欄目完整、可運行地發佈 [CrackProof 內部機制](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/)所用的參考材料。

## 驗證套件

兩項檢查覆蓋 [CrackProof Windows 內部機制](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/) 中的 Python 示例。`run_tests.py` 對參考實現文件運行 31 項比對。`verify_docs.py` 在每種語言的九個 Windows 頁面中執行全部 16 個 Python 代碼塊，每種語言運行 27 項比對。檢查使用固定參考向量與已知答案，不能證明所有輸入或運行時行為。套件按每個文件一頁發佈：

| 文件                | 作用                                               |
| ----------------- | ------------------------------------------------ |
| `primitives.py`   | 滾動密鑰密碼、字節旋轉、LFSR、字符串密碼、頁置亂、按需頁密碼、CRC-32、校驗和、三角調度 |
| `aes_impl.py`     | 帶緩衝區內置密鑰調度的 AES-CBC 解密                           |
| `huffman.py`      | Huffman/LZ 混合解壓器                                 |
| `bytecode_vm.py`  | 逐構建字節碼樁解碼器/解釋器及其逆變換                              |
| `detect.py`       | 基於內容的識別與分類                                       |
| `run_tests.py`    | 參考實現比對工具（31 項比對） |
| `verify_docs.py`  | Markdown 檢查器（三種語言，共 81 項比對） |
| `rust_vectors.rs` | 打印參考輸出的獨立移植 |
| `vectors.txt`     | 檢查使用的 25 條具名參考記錄 |

把參考 Python 文件與 `vectors.txt` 放在一起，然後運行 `python run_tests.py`。腳本會查找自身旁邊的向量文件。預期結果：`all vectors match`。

在文檔倉庫根目錄運行：

```bash
python verification/run_tests.py
python verification/verify_docs.py
```

Markdown 檢查器需要文檔目錄樹，結束時輸出 `all Windows doc snippets verified (3 languages, 48 Python blocks, 81 checks)`。這些檢查覆蓋 Windows Python 示例；Android 偽代碼與非 Python 示例需要另行驗證。

## 參考捕獲

[調試日誌示例](sample-debug-logs.md) 頁發佈從受保護進程捕獲並脫敏的真實 CrackProof 調試日誌：一個功能完整的宿主 EXE（頁加密）、一個原生插件 DLL（僅整體解密）與一個託管 DLL。
