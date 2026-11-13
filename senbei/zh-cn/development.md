---
description: "构建 CLI、桌面 GUI 与 WASM 目标，运行样本库、模糊测试、一致性套件及基准测试。"
icon: hammer
---

# 开发指南

## 编译构建

Senbei 在 `rust-toolchain.toml` 中固定使用 Rust `1.99.1`。直接运行 `cargo build --release` 会构建默认工作区成员（`senbei-cli`）；构建原生桌面工作台请加上 `-p senbei-gui`：

{% tabs %}
{% tab title="CLI 与桌面 GUI" %}
```cmd
cargo build --release
cargo build --release -p senbei-gui
cargo build --release --locked -p senbei-cli -p senbei-gui
```

Windows 下生成的可执行文件位于 `target\release\senbei.exe` 与 `target\release\senbei-gui.exe`（Linux 下为 `target/release/senbei` 与 `target/release/senbei-gui`）。
{% endtab %}

{% tab title="WebAssembly 与前端" %}
```cmd
cargo check --workspace --target wasm32-unknown-unknown
cargo check --manifest-path senbei-wasm/Cargo.toml --target wasm32-unknown-unknown
cd senbei-wasm && wasm-pack build --target web --release --out-dir ../web/pkg -- --locked
npm test --prefix web
```

构建出 `web/pkg` 后，使用本地静态 HTTP 服务器托管 `web/` 目录即可在浏览器中访问。
{% endtab %}
{% endtabs %}

## 测试、模糊测试与 WASM 一致性验证

```cmd
cargo test --release --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

仓库自带的测试套件无需私有样本即可完整通过。当本地存在 `samples/` 样本库时，Windows 基准测试会逐字节比对所有 fixture 的脱壳输出（清理环境时切勿删除 `samples/` 目录或其 junction 目录联接）。

* **本地样本库回归测试器：** 在临时工作目录中生成样本清单与关联提交哈希的 JSON 报告，不会改动任何基准文件：
  ```cmd
  cargo run --release --example corpus_harness -- --emit-manifest samples --manifest-out target/corpus.json
  cargo run --release --example corpus_harness -- --manifest target/corpus.json --report target/corpus-report.json
  ```
* **模糊测试（`fuzz/`）：** 包含六个 `libFuzzer` 目标（`pe_detect`、`pe_parse`、`pe_integrity`、`elf_layout`、`metadata_parse`、`metadata_restore`）及一个确定性冒烟测试程序（`smoke`）：
  ```cmd
  cargo check --manifest-path fuzz/Cargo.toml
  cargo run --release --manifest-path fuzz/Cargo.toml --bin smoke
  ```
  在装有 `cargo-fuzz` 的 nightly 工具链下，`fuzz/run.sh [TARGET] [SECONDS]`（默认参数为 `all` 与 `60`）会自动施加输入大小、运行时间与内存上限。
* **原生与 WASM 字节变换一致性：** 每个任务均在全新的 Node worker 与独立 WebAssembly 实例中运行并比对输出：
  ```sh
  cd senbei-wasm && wasm-pack build --target nodejs --release --out-dir ../target/wasm-parity/pkg -- --locked && cd ..
  SENBEI_WASM_PARITY=1 cargo test --release -p senbei-cli --test wasm_parity
  ```
* **端到端确定性基准测试：** 先预热再按不同线程上限计时运行 CLI，同时开启严格完整性校验并核对各次输出的 SHA-256 完全一致：
  ```cmd
  node scripts/benchmark.mjs target/release/senbei.exe app.exe 3 1,2,4
  node --test scripts/benchmark.test.mjs
  ```

## 环境变量

| 变量名 | 作用 |
| --- | --- |
| `SENBEI_LANG` | 设置 CLI 输出及 GUI 初始界面语言标签（`en`、`zh-CN`、`zh-TW`、`ja`、`ko`） |
| `SENBEI_THREADS` | 并行数据块还原的工作线程上限（`>= 1`；设为 `1` 串行运行，命令行 `--threads` 优先级更高） |
| `SENBEI_SCAN_ALL` | CLI 文件夹扫描时一并探测小于 `4,128` 字节的候选目标文件 |
| `SENBEI_ANDROID_SAMPLES` | 覆盖本地 Android 样本库路径 |
| `SENBEI_REQUIRE_SAMPLES` | 当 `samples/` 不存在或为空时令样本库集成测试直接失败而非跳过 |
| `SENBEI_WASM_PARITY` | 启用 `senbei-cli --test wasm_parity`（设为 `1` 时执行） |
| `SENBEI_WASM_PKG` / `SENBEI_WASM_PARITY_CORPUS` | 覆盖 Node 端 `wasm-pack` 包目录 / 向 `wasm_parity` 传入样本清单路径 |
| `SENBEI_NODE` / `SENBEI_WASM_PARITY_TIMEOUT_MS` | 覆盖 Node 可执行文件路径 / 单任务 worker 超时毫秒数（默认 `120000`，设为 `0` 禁用超时） |
| `DD8_SHIFT` / `SEL_DIAG` | PE `.text` 段 `dd8` 位移调试覆盖值（`99` 表示跳过）与布局选择器 `stderr` 诊断开关（在 `senbei-gui` 中启用时顶部会弹出警告横幅） |

## 仓库目录结构与开发规范

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

* 保持 `senbei-pe`、`senbei-elf` 与 Windows PE 引擎不依赖任何文件系统 I/O，并确保 `senbei-gui` 的 `Workbench` UI 层始终能在 `wasm32-unknown-unknown` 目标下通过编译。
* 所有启发式候选参数都必须经过试解密与结构校验；并行路径与串行路径产出的字节必须完全一致。
* 严禁向仓库提交受保护二进制文件、脱壳产物或可识别具体产品名称的 fixture 文件名。
