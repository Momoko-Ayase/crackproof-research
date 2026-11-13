---
description: "Build CLI, desktop GUI, and WebAssembly targets, run corpus, fuzz, and parity suites, run benchmarks, and set env vars."
icon: hammer
---

# Development

## Building

Senbei pins Rust `1.99.1` in `rust-toolchain.toml`. Plain `cargo build --release` builds the default workspace member (`senbei-cli`); pass `-p senbei-gui` to build the native desktop workbench:

{% tabs %}
{% tab title="CLI & Desktop GUI" %}
```cmd
cargo build --release
cargo build --release -p senbei-gui
cargo build --release --locked -p senbei-cli -p senbei-gui
```

On Windows, binaries are written to `target\release\senbei.exe` and `target\release\senbei-gui.exe` (Linux: `target/release/senbei` and `target/release/senbei-gui`).
{% endtab %}

{% tab title="WebAssembly & Frontend" %}
```cmd
cargo check --workspace --target wasm32-unknown-unknown
cargo check --manifest-path senbei-wasm/Cargo.toml --target wasm32-unknown-unknown
cd senbei-wasm && wasm-pack build --target web --release --out-dir ../web/pkg -- --locked
npm test --prefix web
```

Serve `web/` over a local static HTTP server after building `web/pkg`.
{% endtab %}
{% endtabs %}

## Testing, fuzzing, and WASM parity

```cmd
cargo test --release --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

The tracked test suite runs cleanly without private samples. When a local `samples/` corpus is present, Windows golden tests check byte-for-byte identity across all fixtures (never delete `samples/` directories or junctions during cleanup).

* **Local corpus regression harness:** generates manifests and commit-linked JSON reports in temporary workspaces without modifying goldens:
  ```cmd
  cargo run --release --example corpus_harness -- --emit-manifest samples --manifest-out target/corpus.json
  cargo run --release --example corpus_harness -- --manifest target/corpus.json --report target/corpus-report.json
  ```
* **Bounded fuzzing (`fuzz/`):** six `libFuzzer` targets (`pe_detect`, `pe_parse`, `pe_integrity`, `elf_layout`, `metadata_parse`, `metadata_restore`) plus a deterministic `smoke` runner:
  ```cmd
  cargo check --manifest-path fuzz/Cargo.toml
  cargo run --release --manifest-path fuzz/Cargo.toml --bin smoke
  ```
  On nightly toolchains with `cargo-fuzz`, `fuzz/run.sh [TARGET] [SECONDS]` (defaults: `all`, `60`) enforces input, time, and memory caps.
* **Native/WASM byte-transform parity:** runs each job in a fresh Node worker and WebAssembly instance:
  ```sh
  cd senbei-wasm && wasm-pack build --target nodejs --release --out-dir ../target/wasm-parity/pkg -- --locked && cd ..
  SENBEI_WASM_PARITY=1 cargo test --release -p senbei-cli --test wasm_parity
  ```
* **End-to-end deterministic timing:** measures warm-up plus timed CLI runs across thread caps while verifying strict integrity and identical output SHA-256 digests:
  ```cmd
  node scripts/benchmark.mjs target/release/senbei.exe app.exe 3 1,2,4
  node --test scripts/benchmark.test.mjs
  ```

## Environment variables

| Variable | Effect |
| --- | --- |
| `SENBEI_LANG` | Display language tag (`en`, `zh-CN`, `zh-TW`, `ja`, `ko`) for CLI output and initial GUI locale |
| `SENBEI_THREADS` | Worker thread limit (`>= 1`) for parallel block recovery (`1` runs sequentially; overridden by `--threads`) |
| `SENBEI_SCAN_ALL` | Probe target-named files below `4,128` bytes during CLI folder scans |
| `SENBEI_ANDROID_SAMPLES` | Override path to the local Android sample corpus |
| `SENBEI_REQUIRE_SAMPLES` | Fail corpus integration tests instead of skipping when `samples/` is absent or empty |
| `SENBEI_WASM_PARITY` | Enable `senbei-cli --test wasm_parity` (`1` to run) |
| `SENBEI_WASM_PKG` / `SENBEI_WASM_PARITY_CORPUS` | Override Node `wasm-pack` package dir / supply a corpus manifest to `wasm_parity` |
| `SENBEI_NODE` / `SENBEI_WASM_PARITY_TIMEOUT_MS` | Override Node binary path / per-job worker timeout in ms (default `120000`, `0` disables) |
| `DD8_SHIFT` / `SEL_DIAG` | Debug overrides for PE `.text` `dd8` shift (`99` skips) and layout-selector stderr diagnostics (flagged with a warning banner in `senbei-gui`) |

## Repository layout and hard rules

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

* Keep `senbei-pe`, `senbei-elf`, and the Windows PE engine free of filesystem I/O, and keep `senbei-gui`'s `Workbench` UI compiling on `wasm32-unknown-unknown`.
* Trial and validate every heuristic candidate; deterministic parallel and sequential paths must emit identical bytes.
* Never commit protected binaries, restored binaries, or product-identifying fixture names.
