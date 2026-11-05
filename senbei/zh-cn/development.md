---
description: "Senbei 工作区的构建、测试与贡献流程。"
---

# 开发

## 构建

要求 Rust 1.99.1，已在 `rust-toolchain.toml` 中固定。用 `cargo build --release` 构建 CLI；在 Windows 上二进制写到 `target/release/senbei.exe`。

工作区 crate 在 API 保持纯净的范围内是可移植的。浏览器绑定在工作区之外，用 `cargo check --manifest-path senbei-wasm/Cargo.toml` 检查，或用 `wasm-pack` 构建浏览器版。

## 测试

```cmd
cargo test --release --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

纳入版本控制的测试套件在没有受保护样本时也能安全运行。可选的本地 `samples/` 语料由用户管理，被忽略的 `test/` 文件夹可用于真实的 Windows 与 Android 运行。

对 Android 包一次只运行一条命令，因为受保护的 `.so` 可能达数百 MB。APK、APKS、XAPK 测试先读 ZIP 清单，只提取 `.so` 与 `global-metadata.dat` 条目。

## 本地语料报告

开发树包含由清单驱动的测试工具。从仓库根目录运行，以记录本地 Git 提交与工作树是否有改动。报告还包含清单哈希、逐案例输出哈希、完整性结果与耗时。工具不上传任何内容，恢复文件仅存在于临时工作区。

```cmd
cargo run --release --example corpus_harness -- --emit-manifest samples --manifest-out target/corpus.json
cargo run --release --example corpus_harness -- --manifest target/corpus.json --report target/corpus-report.json
```

生成器列出指定根目录下的直接输入，不跟随 junction，也不扫描无关目录。明确添加 `--android-app DIR` 可纳入带有现有 sidecar 的解压应用树。运行前先检查生成的清单。最小手写案例如下：

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

除绝对路径外，路径均相对于清单解析。成功案例默认需要黄金文件或预期 SHA-256。黄金文件缺失或过期会使测试失败，工具不会重新生成它们。`expect_failure` 仅覆盖恢复阶段错误，不包括文件缺失、清单格式错误或返回的内部 panic。恢复产物与预期失败分开计数。`allow_missing_golden` 仅用于未经验证的研究，不代表已通过黄金对比。`--commit SHA` 记录调用方提供的标签；报告会标明来源，不会将其当作由 Git 证明的构建。

## Fuzzing 与原生/WASM 一致性

```cmd
cargo check --manifest-path fuzz/Cargo.toml
cargo run --release --manifest-path fuzz/Cargo.toml --bin smoke
```

确定性冒烟测试使用有边界的生成输入。六个 libFuzzer 目标覆盖 PE 检测、PE 解析、PE 完整性、ELF 布局、元数据识别与元数据恢复。完整 fuzzing 需要 `cargo-fuzz` 与支持它的 nightly 工具链；`fuzz/run.sh TARGET SECONDS` 会选用 nightly，并设置输入、时间与内存上限。冒烟通过不等于执行过 fuzzing 活动。当前不包含 ZIP fuzzing。

字节变换一致性测试需要先构建 Node 绑定，再明确启用测试。以下命令使用 POSIX shell，包括 Git Bash：

```sh
cd senbei-wasm
wasm-pack build --target nodejs --release --out-dir ../target/wasm-parity/pkg -- --locked
cd ..
SENBEI_WASM_PARITY=1 cargo test --release -p senbei-cli --test wasm_parity
```

每个一致性任务使用新的 worker 与 WASM 实例，发生 trap 后也不会复用。把 `SENBEI_WASM_PARITY_CORPUS` 设为私有测试清单，可同时比较其中的 PE 与元数据案例。`SENBEI_WASM_PKG` 可覆盖包目录。未明确启用时，测试会报告跳过；公开 CI 会启用合成输入检查。该测试比较共同支持的字节变换，不验证 Android 浏览器恢复或运行时可加载性。

## 可重复的计时

开发树包含端到端基准测试。先构建 CLI，再传入其路径与明确的输入文件或文件夹。在非 Windows 主机上，去掉二进制路径中的 `.exe`。

```cmd
node scripts/benchmark.mjs target/release/senbei.exe app.exe 3 1,2,4
node --test scripts/benchmark.test.mjs
```

该示例在每个线程上限下先预热一次，再测量后续三次运行。报告中的进程时间包括启动与 I/O，不是独立算法的耗时。每次运行使用新的临时输出树，启用严格完整性检查，并将输出哈希与首次运行比较。恢复失败、没有输出或字节变化都会中止基准测试。临时输出会被移除；JSON 报告留在标准输出中。

改变缓冲区所有权、复制操作或流水线并行方式之前，先取得这些测量结果。运行更快不是正确性证据，线程上限也不保证加速。

## 环境变量

* `DD8_SHIFT` 覆盖 PE 页 XOR 移位；`99` 跳过该阶段。
* `SEL_DIAG` 打印 PE 布局选择器诊断。
* `SENBEI_THREADS` 限制确定性块并行的扇出；`1` 强制顺序参考路径。
* `SENBEI_SCAN_ALL` 允许探测低于大小下限的选定目标名；它不会启用任意文件名。
* `SENBEI_ANDROID_SAMPLES` 覆盖 Android 样本语料位置。

## 约定

格式 crate 不沾染文件系统 I/O 与保护方案专属逻辑。Windows 引擎代码在 `senbei-engine/src/windows/` 下，Android 引擎代码在 `senbei-engine/src/android/` 下，共享代码直接在各 crate 的 `src/` 下。

布局启发式必须对每个候选试解再验证。验证失败是错误或落空，绝不是静默接受的偏移。

输出必须相对可用黄金语料保持逐字节一致。改动流水线或元数据布局后，运行完整的工作区测试。

文件夹扫描使用明确的目标名来避免打开批量资产。外置 `.exe._`、`.dll._` 文件是其同级 stub 的辅助数据，不是独立的扫描目标。

## 仓库布局

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

## Web 构建

```cmd
cd senbei-wasm
wasm-pack build --target web --release --out-dir ../web/pkg
```

构建后用静态 HTTP 服务器托管 `web/`。浏览器版从不上传输入文件。
