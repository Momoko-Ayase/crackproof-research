---
description: "Senbei 工作區的構建、測試與貢獻流程。"
---

# 開發

## 構建

要求 Rust 1.98.1，已在 `rust-toolchain.toml` 中固定。用 `cargo build --release` 構建 CLI；在 Windows 上二進制寫到 `target/release/senbei.exe`。

工作區 crate 在 API 保持純淨的範圍內是可移植的。瀏覽器綁定在工作區之外，用 `cargo check --manifest-path senbei-wasm/Cargo.toml` 檢查，或用 `wasm-pack` 構建瀏覽器版。

## 測試

```cmd
cargo test --release --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

納入版本控制的測試套件在沒有受保護樣本時也能安全運行。可選的本地 `samples/` 語料由用戶管理，被忽略的 `test/` 文件夾可用於真實的 Windows 與 Android 運行。

對 Android 包一次只運行一條命令，因為受保護的 `.so` 可能達數百 MB。APK、APKS、XAPK 測試先讀 ZIP 清單，只提取 `.so` 與 `global-metadata.dat` 條目。

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
