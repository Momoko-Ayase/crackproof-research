---
description: "Build, test, and contribution workflow for the Senbei workspace."
---

# Development

## Building

Rust 1.99.1 is required and pinned in `rust-toolchain.toml`. Build the CLI with `cargo build --release`; the binary is written to `target/release/senbei.exe` on Windows.

The workspace crates are portable where their APIs are pure. The browser binding is outside the workspace and is checked with `cargo check --manifest-path senbei-wasm/Cargo.toml` or built with `wasm-pack`.

## Testing

```cmd
cargo test --release --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

The tracked test suite is safe without protected samples. The optional local `samples/` corpus is user-managed, and the ignored `test/` folder can be used for real Windows and Android runs.

For an Android package, run one command at a time because a protected `.so` can be hundreds of megabytes. APK, APKS, and XAPK tests read the ZIP manifest first and extract only `.so` and `global-metadata.dat` entries.

## Local corpus reports

The development tree includes a manifest-driven harness. Run it from the repository root to record the local Git commit and dirty-tree status. Reports also include the manifest hash, per-case output hashes, integrity results, and elapsed time. Nothing is uploaded, and restored files live only in temporary workspaces.

```cmd
cargo run --release --example corpus_harness -- --emit-manifest samples --manifest-out target/corpus.json
cargo run --release --example corpus_harness -- --manifest target/corpus.json --report target/corpus-report.json
```

The emitter lists immediate inputs under the supplied root. It doesn't follow junctions or scan unrelated folders. Add an explicit `--android-app DIR` to include an extracted app tree with its existing sidecars. Review the emitted manifest before running it. A minimal hand-written case is:

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

Paths are relative to the manifest unless absolute. Successful cases require a golden or expected SHA-256 by default. Missing or stale goldens fail; the harness doesn't regenerate them. `expect_failure` covers restoration-stage errors, not missing files, malformed manifests, or surfaced internal panics. Recovered outputs and expected failures have separate counts. Only opt out with `allow_missing_golden` for unverified research, not to claim a golden-checked result. `--commit SHA` records a caller-supplied label; the report identifies its source rather than presenting it as a Git-attested build.

## Fuzzing and native/WASM parity

```cmd
cargo check --manifest-path fuzz/Cargo.toml
cargo run --release --manifest-path fuzz/Cargo.toml --bin smoke
```

The deterministic smoke runner exercises bounded generated inputs. The six libFuzzer targets cover PE detection, PE parsing, PE integrity, ELF layout, metadata identification, and metadata restoration. Full fuzzing requires `cargo-fuzz` and a supported nightly toolchain; `fuzz/run.sh TARGET SECONDS` selects nightly and applies input, time, and memory ceilings. A smoke pass isn't a fuzz campaign. ZIP fuzzing isn't included.

For byte-transform parity, build Node bindings and explicitly enable the test. These commands use a POSIX shell, including Git Bash:

```sh
cd senbei-wasm
wasm-pack build --target nodejs --release --out-dir ../target/wasm-parity/pkg -- --locked
cd ..
SENBEI_WASM_PARITY=1 cargo test --release -p senbei-cli --test wasm_parity
```

Each parity job gets a fresh worker and WASM instance, including after a trap. Set `SENBEI_WASM_PARITY_CORPUS` to a private harness manifest to compare its PE and metadata cases too. `SENBEI_WASM_PKG` overrides the package directory. Without explicit enablement, the test reports that it skipped; public CI enables the synthetic check. This compares the common byte transforms, not Android browser restoration or runtime loadability.

## Reproducible timing

The development tree includes an end-to-end benchmark. Build the CLI first, then pass its path and an explicit input file or folder. On non-Windows hosts, omit `.exe` from the binary path.

```cmd
node scripts/benchmark.mjs target/release/senbei.exe app.exe 3 1,2,4
node --test scripts/benchmark.test.mjs
```

The benchmark performs one warm-up per thread cap and measures three subsequent runs in this example. It reports process time, including startup and I/O, rather than isolated algorithm time. Every run uses a new temporary output tree, enables strict integrity, and checks output hashes against the first run. Failed restores, empty output sets, or changed bytes stop the benchmark. Temporary outputs are removed; the JSON report stays on standard output.

Use these measurements before changing buffer ownership, copying, or pipeline parallelism. A faster run isn't evidence of correctness, and a thread cap doesn't promise a speedup.

## Environment variables

* `DD8_SHIFT` overrides the PE page-XOR shift; `99` skips that stage.
* `SEL_DIAG` prints PE layout-selector diagnostics.
* `SENBEI_THREADS` caps deterministic block fan-out; `1` forces the sequential reference path.
* `SENBEI_SCAN_ALL` enables probing selected target names below the size floor; it never enables arbitrary filenames.
* `SENBEI_ANDROID_SAMPLES` overrides the Android sample corpus location.

## Conventions

Format crates stay free of filesystem I/O and protection-specific logic. Windows engine code lives below `senbei-engine/src/windows/`, Android engine code below `senbei-engine/src/android/`, and shared code stays directly under each crate's `src/`.

Layout heuristics must trial and validate every candidate. A failed validation is an error or a fall-through, never a silently accepted offset.

Outputs must remain byte-identical against the available golden corpus. Run the full workspace tests after changing a pipeline or a metadata layout.

Folder scanning uses explicit target names to avoid opening bulk assets. External `.exe._` and `.dll._` files are auxiliary data for their sibling stubs, not independent scan targets.

## Repository layout

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

## Web build

```cmd
cd senbei-wasm
wasm-pack build --target web --release --out-dir ../web/pkg
```

Serve `web/` with a static HTTP server after the build. The browser never uploads input files.
