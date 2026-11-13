---
description: "CLI・GUI・WASM のビルド、コーパス・ファジング・パリティ検証、ベンチマーク、環境変数。"
icon: hammer
---

# 開発

## ビルド手順

Senbei は `rust-toolchain.toml` で Rust `1.99.1` を固定しています。通常の `cargo build --release` は既定のワークスペースメンバー（`senbei-cli`）をビルドします。ネイティブデスクトップワークベンチをビルドするには `-p senbei-gui` を指定してください。

{% tabs %}
{% tab title="CLI とデスクトップ GUI" %}
```cmd
cargo build --release
cargo build --release -p senbei-gui
cargo build --release --locked -p senbei-cli -p senbei-gui
```

Windows では `target\release\senbei.exe` と `target\release\senbei-gui.exe` に出力されます（Linux では `target/release/senbei` と `target/release/senbei-gui`）。
{% endtab %}

{% tab title="WebAssembly とフロントエンド" %}
```cmd
cargo check --workspace --target wasm32-unknown-unknown
cargo check --manifest-path senbei-wasm/Cargo.toml --target wasm32-unknown-unknown
cd senbei-wasm && wasm-pack build --target web --release --out-dir ../web/pkg -- --locked
npm test --prefix web
```

`web/pkg` のビルド後、ローカルの静的 HTTP サーバーで `web/` を配信します。
{% endtab %}
{% endtabs %}

## テスト・ファジング・WASM パリティ検証

```cmd
cargo test --release --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

リポジトリに含まれるテストスイートは非公開サンプルなしでもすべて通過します。ローカルに `samples/` コーパスが存在する場合、Windows のゴールデンテストが全 fixture のバイト単位の一致を検証します（クリーンアップ時などに `samples/` ディレクトリやジャンクションを決して削除しないでください）。

* **ローカルコーパス回帰ハーネス:** ゴールデンファイルを変更せず、一時作業領域上でマニフェストとコミット紐付きの JSON レポートを生成します。
  ```cmd
  cargo run --release --example corpus_harness -- --emit-manifest samples --manifest-out target/corpus.json
  cargo run --release --example corpus_harness -- --manifest target/corpus.json --report target/corpus-report.json
  ```
* **上限付きファジング（`fuzz/`）:** 6つの `libFuzzer` ターゲット（`pe_detect`、`pe_parse`、`pe_integrity`、`elf_layout`、`metadata_parse`、`metadata_restore`）と決定論的な `smoke` ランナーを備えています。
  ```cmd
  cargo check --manifest-path fuzz/Cargo.toml
  cargo run --release --manifest-path fuzz/Cargo.toml --bin smoke
  ```
  `cargo-fuzz` を導入した nightly ツールチェーン環境では、`fuzz/run.sh [TARGET] [SECONDS]`（既定値：`all`、`60`）を使えば、入力サイズ・実行時間・メモリ上限付きで実行できます。
* **ネイティブ／WASM バイト変換パリティ検証:** 各ジョブを毎回新しい Node worker と WebAssembly インスタンス上で実行し、出力の一致を検証します。
  ```sh
  cd senbei-wasm && wasm-pack build --target nodejs --release --out-dir ../target/wasm-parity/pkg -- --locked && cd ..
  SENBEI_WASM_PARITY=1 cargo test --release -p senbei-cli --test wasm_parity
  ```
* **エンドツーエンドの決定論的ベンチマーク:** スレッド数上限を変えながらウォームアップと計測実行を行い、厳格な整合性チェックと出力 SHA-256 ダイジェストの完全一致を同時に確認します。
  ```cmd
  node scripts/benchmark.mjs target/release/senbei.exe app.exe 3 1,2,4
  node --test scripts/benchmark.test.mjs
  ```

## 環境変数

| 変数名 | 効果 |
| --- | --- |
| `SENBEI_LANG` | CLI 出力および GUI 初回起動時の表示言語タグ（`en`、`zh-CN`、`zh-TW`、`ja`、`ko`） |
| `SENBEI_THREADS` | 並列ブロック復元時のワーカースレッド数上限（`>= 1`、`1` で逐次実行、`--threads` 指定時はそちらが優先） |
| `SENBEI_SCAN_ALL` | CLI のフォルダー走査時に `4,128` バイト未満の対象拡張子ファイルもプローブする |
| `SENBEI_ANDROID_SAMPLES` | ローカルの Android サンプルコーパスへのパスを上書き指定する |
| `SENBEI_REQUIRE_SAMPLES` | `samples/` が存在しないか空の場合にコーパス統合テストをスキップせず失敗させる |
| `SENBEI_WASM_PARITY` | `senbei-cli --test wasm_parity` を有効化する（`1` で実行） |
| `SENBEI_WASM_PKG` / `SENBEI_WASM_PARITY_CORPUS` | Node 用 `wasm-pack` パッケージディレクトリの上書き／`wasm_parity` へのコーパスマニフェスト指定 |
| `SENBEI_NODE` / `SENBEI_WASM_PARITY_TIMEOUT_MS` | Node バイナリパスの上書き／ジョブ単位の worker タイムアウト値（ミリ秒、既定 `120000`、`0` で無効化） |
| `DD8_SHIFT` / `SEL_DIAG` | PE `.text` の `dd8` シフト量強制指定（`99` でスキップ）およびレイアウト選択器の `stderr` 診断出力（`senbei-gui` では警告バナーが表示されます） |

## リポジトリ構成と開発上の必須ルール

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

* `senbei-pe`、`senbei-elf`、および Windows PE エンジンにはファイルシステム I/O を持ち込まず、`senbei-gui` の `Workbench` UI が `wasm32-unknown-unknown` ターゲットでコンパイルできる状態を維持してください。
* ヒューリスティックな候補はすべて試行復号と検証を通し、並列実行パスと逐次実行パスで完全に同一のバイト列を出力させてください。
* 保護されたバイナリ、復元済みバイナリ、または特定の製品名が判別できる fixture 名は一切コミットしないでください。
