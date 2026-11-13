---
description: "建置 CLI、桌面版 GUI 與 WASM 目標，執行測試與模糊測試套件、基準測試與環境變數。"
icon: hammer
---

# 開發指南

## 建置專案

Senbei 於 `rust-toolchain.toml` 固定使用 Rust `1.99.1`。直接執行 `cargo build --release` 會建置預設 workspace 成員（`senbei-cli`）；若要建置原生桌面工作台，請加上 `-p senbei-gui`：

{% tabs %}
{% tab title="CLI 與桌面版 GUI" %}
```cmd
cargo build --release
cargo build --release -p senbei-gui
cargo build --release --locked -p senbei-cli -p senbei-gui
```

在 Windows 上，執行檔會輸出至 `target\release\senbei.exe` 與 `target\release\senbei-gui.exe`（Linux 為 `target/release/senbei` 與 `target/release/senbei-gui`）。
{% endtab %}

{% tab title="WebAssembly 與前端" %}
```cmd
cargo check --workspace --target wasm32-unknown-unknown
cargo check --manifest-path senbei-wasm/Cargo.toml --target wasm32-unknown-unknown
cd senbei-wasm && wasm-pack build --target web --release --out-dir ../web/pkg -- --locked
npm test --prefix web
```

建置完 `web/pkg` 後，請以本機靜態 HTTP 伺服器開啟 `web/` 目錄。
{% endtab %}
{% endtabs %}

## 測試、模糊測試與 WASM 一致性驗證

```cmd
cargo test --release --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

內建測試套件無須私有樣本即可完整執行。若本機存在 `samples/` 樣本集，Windows 基準測試（golden test）會針對所有 fixture 逐位元組比對輸出結果（清理環境時切勿刪除 `samples/` 目錄或 NTFS junction 連結）。

* **本機樣本集迴歸測試工具：** 在暫存工作區產生清單與綁定 commit 的 JSON 報告，不會修改基準檔案：
  ```cmd
  cargo run --release --example corpus_harness -- --emit-manifest samples --manifest-out target/corpus.json
  cargo run --release --example corpus_harness -- --manifest target/corpus.json --report target/corpus-report.json
  ```
* **具資源上限的模糊測試（`fuzz/`）：** 包含六個 `libFuzzer` 目標（`pe_detect`、`pe_parse`、`pe_integrity`、`elf_layout`、`metadata_parse`、`metadata_restore`）與一個確定性的 `smoke` 執行器：
  ```cmd
  cargo check --manifest-path fuzz/Cargo.toml
  cargo run --release --manifest-path fuzz/Cargo.toml --bin smoke
  ```
  在安裝 `cargo-fuzz` 的 nightly 工具鏈上，`fuzz/run.sh [TARGET] [SECONDS]`（預設為 `all`、`60`）會強制套用輸入大小、執行時間與記憶體上限。
* **原生與 WASM 位元組轉換一致性：** 每個工作皆在全新的 Node worker 與 WebAssembly 執行個體中獨立執行：
  ```sh
  cd senbei-wasm && wasm-pack build --target nodejs --release --out-dir ../target/wasm-parity/pkg -- --locked && cd ..
  SENBEI_WASM_PARITY=1 cargo test --release -p senbei-cli --test wasm_parity
  ```
* **端對端確定性計時：** 執行暖機與計時測試，測量不同執行緒上限下的 CLI 執行耗時，同時驗證嚴格完整性檢查通過且輸出 SHA-256 雜湊值完全一致：
  ```cmd
  node scripts/benchmark.mjs target/release/senbei.exe app.exe 3 1,2,4
  node --test scripts/benchmark.test.mjs
  ```

## 環境變數

| 變數名稱 | 作用 |
| --- | --- |
| `SENBEI_LANG` | 設定 CLI 輸出與 GUI 初始語系的顯示語言標籤（`en`、`zh-CN`、`zh-TW`、`ja`、`ko`） |
| `SENBEI_THREADS` | 平行區塊還原的工作執行緒上限（`>= 1`；設為 `1` 時循序執行，會被 `--threads` 覆寫） |
| `SENBEI_SCAN_ALL` | 在 CLI 資料夾掃描期間一併探測小於 `4,128` 位元組的目標檔名檔案 |
| `SENBEI_ANDROID_SAMPLES` | 覆寫本機 Android 樣本集路徑 |
| `SENBEI_REQUIRE_SAMPLES` | 當 `samples/` 不存在或為空時，讓樣本集整合測試直接失敗而非略過 |
| `SENBEI_WASM_PARITY` | 啟用 `senbei-cli --test wasm_parity`（設為 `1` 即執行） |
| `SENBEI_WASM_PKG` / `SENBEI_WASM_PARITY_CORPUS` | 覆寫 Node `wasm-pack` 套件目錄／提供樣本集清單給 `wasm_parity` |
| `SENBEI_NODE` / `SENBEI_WASM_PARITY_TIMEOUT_MS` | 覆寫 Node 執行檔路徑／設定單一工作 worker 逾時毫秒數（預設 `120000`，`0` 代表停用） |
| `DD8_SHIFT` / `SEL_DIAG` | PE `.text` `dd8` 位移量的除錯覆寫值（`99` 代表略過）與版面選擇器 `stderr` 診斷輸出（設定時 `senbei-gui` 會顯示頂端警告橫幅） |

## 專案目錄結構與核心規範

```text
senbei-cli/       CLI binary, corpus_harness example, and integration tests
senbei-gui/       native eframe/wgpu desktop workbench (Windows & Linux)
senbei-i18n/      five-language message, step, term, and CLI catalog
senbei-io/        scanning, companion splicing, APK streaming, observer/cancel hooks
senbei-engine/    Windows PE and Android ELF pipelines, profiles, and research traces
senbei-crypto/    Windows and Android ciphers, AES, bytecode VM, and Huffman/LZ
senbei-metadata/  shared structural v31 and Android seeded/embedded metadata recovery
senbei-pe/        pure PE32/PE32+ parser and RVA mapper
senbei-elf/       pure ELF64 parser, SysV/GNU hash builders, and PT_LOAD layout helpers
senbei-wasm/      standalone WebAssembly bindings
web/              static browser frontend and unit tests
fuzz/             libFuzzer targets and deterministic smoke runner
scripts/          reproducible benchmark runner and tests
```

* 維持 `senbei-pe`、`senbei-elf` 與 Windows PE 引擎零檔案系統 I/O，並確保 `senbei-gui` 的 `Workbench` UI 可在 `wasm32-unknown-unknown` 目標下通過編譯。
* 所有啟發式候選參數皆須經過試算與結構驗證；平行路徑與循序路徑必須產出完全相同的位元組。
* 嚴禁提交受保護的二進位檔、還原後的二進位檔，或足以識別商業產品的 fixture 名稱。
