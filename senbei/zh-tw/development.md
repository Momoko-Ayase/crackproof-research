---
description: "Senbei 工作區的構建、測試與貢獻流程。"
---

# 開發

## 構建

要求 Rust 1.99.1，已在 `rust-toolchain.toml` 中固定。用 `cargo build --release` 構建 CLI；在 Windows 上二進制寫到 `target/release/senbei.exe`。

工作區 crate 在 API 保持純淨的範圍內是可移植的。瀏覽器綁定在工作區之外，用 `cargo check --manifest-path senbei-wasm/Cargo.toml` 檢查，或用 `wasm-pack` 構建瀏覽器版。

## 測試

```cmd
cargo test --release --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

納入版本控制的測試套件在沒有受保護樣本時也能安全運行。可選的本地 `samples/` 語料由用戶管理，被忽略的 `test/` 文件夾可用於真實的 Windows 與 Android 運行。

對 Android 包一次只運行一條命令，因為受保護的 `.so` 可能達數百 MB。APK、APKS、XAPK 測試先讀 ZIP 清單，只提取 `.so` 與 `global-metadata.dat` 條目。

## 本地語料報告

開發樹包含由清單驅動的測試工具。從倉庫根目錄運行，以記錄本地 Git 提交與工作樹是否有改動。報告還包含清單哈希、逐案例輸出哈希、完整性結果與耗時。工具不上傳任何內容，恢復文件僅存在於臨時工作區。

```cmd
cargo run --release --example corpus_harness -- --emit-manifest samples --manifest-out target/corpus.json
cargo run --release --example corpus_harness -- --manifest target/corpus.json --report target/corpus-report.json
```

生成器列出指定根目錄下的直接輸入，不跟隨 junction，也不掃描無關目錄。明確添加 `--android-app DIR` 可納入帶有現有 sidecar 的解壓應用樹。運行前先檢查生成的清單。最小手寫案例如下：

```json
{
  "schema": "senbei-corpus-harness/1",
  "cases": [
    {
      "id": "native-pe-1",
      "kind": "pe",
      "input": "app.exe",
      "golden": "app.golden.exe"
    }
  ]
}
```

除絕對路徑外，路徑均相對於清單解析。成功案例默認需要黃金文件或預期 SHA-256。黃金文件缺失或過期會使測試失敗，工具不會重新生成它們。`expect_failure` 僅覆蓋恢復階段錯誤，不包括文件缺失、清單格式錯誤或返回的內部 panic。恢復產物與預期失敗分開計數。`allow_missing_golden` 僅用於未經驗證的研究，不代表已通過黃金對比。`--commit SHA` 記錄調用方提供的標籤；報告會標明來源，不會將其當作由 Git 證明的構建。

## Fuzzing 與原生/WASM 一致性

```cmd
cargo check --manifest-path fuzz/Cargo.toml
cargo run --release --manifest-path fuzz/Cargo.toml --bin smoke
```

確定性冒煙測試使用有邊界的生成輸入。六個 libFuzzer 目標覆蓋 PE 檢測、PE 解析、PE 完整性、ELF 佈局、元數據識別與元數據恢復。完整 fuzzing 需要 `cargo-fuzz` 與支持它的 nightly 工具鏈；`fuzz/run.sh TARGET SECONDS` 會選用 nightly，並設置輸入、時間與內存上限。冒煙通過不等於執行過 fuzzing 活動。當前不包含 ZIP fuzzing。

字節變換一致性測試需要先構建 Node 綁定，再明確啟用測試。以下命令使用 POSIX shell，包括 Git Bash：

```sh
cd senbei-wasm
wasm-pack build --target nodejs --release --out-dir ../target/wasm-parity/pkg -- --locked
cd ..
SENBEI_WASM_PARITY=1 cargo test --release -p senbei-cli --test wasm_parity
```

每個一致性任務使用新的 worker 與 WASM 實例，發生 trap 後也不會複用。把 `SENBEI_WASM_PARITY_CORPUS` 設為私有測試清單，可同時比較其中的 PE 與元數據案例。`SENBEI_WASM_PKG` 可覆蓋包目錄。未明確啟用時，測試會報告跳過；公開 CI 會啟用合成輸入檢查。該測試比較共同支持的字節變換，不驗證 Android 瀏覽器恢復或運行時可加載性。

## 可重複的計時

開發樹包含端到端基準測試。先構建 CLI，再傳入其路徑與明確的輸入文件或文件夾。在非 Windows 主機上，去掉二進制路徑中的 `.exe`。

```cmd
node scripts/benchmark.mjs target/release/senbei.exe app.exe 3 1,2,4
node --test scripts/benchmark.test.mjs
```

該示例在每個線程上限下先預熱一次，再測量後續三次運行。報告中的進程時間包括啟動與 I/O，不是獨立算法的耗時。每次運行使用新的臨時輸出樹，啟用嚴格完整性檢查，並將輸出哈希與首次運行比較。恢復失敗、沒有輸出或字節變化都會中止基準測試。臨時輸出會被移除；JSON 報告留在標準輸出中。

改變緩衝區所有權、複製操作或流水線並行方式之前，先取得這些測量結果。運行更快不是正確性證據，線程上限也不保證加速。

## 環境變量

* `DD8_SHIFT` 覆蓋 PE 頁 XOR 移位；`99` 跳過該階段。
* `SEL_DIAG` 打印 PE 佈局選擇器診斷。
* `SENBEI_THREADS` 限制確定性塊並行的扇出；`1` 強制順序參考路徑。
* `SENBEI_SCAN_ALL` 允許探測低於大小下限的選定目標名；它不會啟用任意文件名。
* `SENBEI_ANDROID_SAMPLES` 覆蓋 Android 樣本語料位置。

## 約定

格式 crate 不沾染文件系統 I/O 與保護方案專屬邏輯。Windows 引擎代碼在 `senbei-engine/src/windows/` 下，Android 引擎代碼在 `senbei-engine/src/android/` 下，共享代碼直接在各 crate 的 `src/` 下。

佈局啟發式必須對每個候選試解再驗證。驗證失敗是錯誤或落空，絕不是靜默接受的偏移。

輸出必須相對可用黃金語料保持逐字節一致。改動流水線或元數據佈局後，運行完整的工作區測試。

文件夾掃描使用明確的目標名來避免打開批量資產。外置 `.exe._`、`.dll._` 文件是其同級 stub 的輔助數據，不是獨立的掃描目標。

## 倉庫佈局

```text
senbei-cli/       command-line binary and integration tests
senbei-crypto/    Windows and Android crypto primitives
senbei-elf/       ELF parsing, mapping, and dynamic-table helpers
senbei-engine/    Windows and Android unpacking engines
senbei-io/        filesystem, package, scanning, and platform adapters
senbei-metadata/  shared, Windows, and Android metadata restoration
senbei-pe/        PE parsing, data directories, and RVA mapping
senbei-wasm/      browser bindings and its own lockfile
web/              static browser frontend
samples/          optional local corpus
```

## Web 構建

```cmd
cd senbei-wasm
wasm-pack build --target web --release --out-dir ../web/pkg
```

構建後用靜態 HTTP 服務器託管 `web/`。瀏覽器版從不上傳輸入文件。
