---
description: "可執行的 Python 參考實作、測試向量、Markdown 驗證器與去識別化除錯記錄。"
icon: flask
---

# 驗證與參考實作

本區收錄對應 [CrackProof for Windows 內部機制](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/) 的完整可執行參考檔案與測試向量，以及去識別化的執行階段除錯記錄。

## 自動化驗證套件

儲存庫內建兩項自動化檢查，用於驗證所有 Windows 資料轉換實作：

* **`run_tests.py`（31 項比對）：** 執行 `verification/` 底下的獨立 Python 模組，逐一比對 `vectors.txt` 中的 25 筆標準測試記錄（由 `rust_vectors.rs` 產生）。
* **`verify_docs.py`（5 種語言、80 個 Python 區塊、135 項比對）：** 從五種語言版本（`en`、`zh-cn`、`zh-tw`、`ja`、`ko`）各自的九篇資料轉換頁面中擷取並執行全部 16 個 Python 程式碼區塊，每種語言執行 27 項測試向量比對。

```bash
python verification/run_tests.py
python verification/verify_docs.py
```

預期結尾輸出為 `all vectors match` 與 `all Windows doc snippets verified (5 languages, 80 Python blocks, 135 checks)`。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-code"></i></td><td><strong>primitives.py</strong></td><td>滾動式 XOR 鏈、位元旋轉、LFSR、字串加密、頁面打亂、按需頁面加密、CRC-32 與三角金鑰排程。</td><td><a href="primitives.py.md">primitives.py</a></td></tr><tr><td><i class="fa-key"></i></td><td><strong>aes_impl.py</strong></td><td>採用緩衝區內排程與 GF(2⁸) 反向 T-table 的零 IV AES-CBC 解密實作。</td><td><a href="aes_impl.py.md">aes_impl.py</a></td></tr><tr><td><i class="fa-file-zipper"></i></td><td><strong>huffman.py</strong></td><td>3 位元組節點 Huffman 樹解碼器與四模式字面值／重複填值／LZ 解壓縮器。</td><td><a href="huffman.py.md">huffman.py</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>bytecode_vm.py</strong></td><td>九個 opcode 的建置專屬 <code>AL</code> x86 stub 解析器、直譯器、256 位元組 LUT 建構器與反函數。</td><td><a href="bytecode_vm.py.md">bytecode_vm.py</a></td></tr><tr><td><i class="fa-fingerprint"></i></td><td><strong>detect.py</strong></td><td>基於檔案內容的 <code>KONN</code> 標頭 KDF 辨識，以及 PE32/PE32+ 原生／Managed 分類。</td><td><a href="detect.py.md">detect.py</a></td></tr><tr><td><i class="fa-circle-check"></i></td><td><strong>run_tests.py</strong></td><td>對照 <code>vectors.txt</code> 執行 31 項比對的獨立測試執行器。</td><td><a href="run_tests.py.md">run_tests.py</a></td></tr><tr><td><i class="fa-list-check"></i></td><td><strong>verify_docs.py</strong></td><td>支援五種語言的 Markdown Python 擷取與驗證工具（80 個區塊、135 項檢查）。</td><td><a href="verify_docs.py.md">verify_docs.py</a></td></tr><tr><td><i class="fa-gears"></i></td><td><strong>rust_vectors.rs</strong></td><td>產生 <code>vectors.txt</code> 標準測試記錄的獨立 Rust 移植實作。</td><td><a href="rust_vectors.rs.md">rust_vectors.rs</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>vectors.txt</strong></td><td>25 筆具名十六進位與結構測試記錄。</td><td><a href="vectors.txt.md">vectors.txt</a></td></tr><tr><td><i class="fa-file-lines"></i></td><td><strong>除錯記錄範例</strong></td><td>取自頁面加密宿主 EXE、原生外掛 DLL 與 Managed DLL 的去識別化執行階段追蹤記錄。</td><td><a href="sample-debug-logs.md">除錯記錄範例</a></td></tr></tbody></table>
