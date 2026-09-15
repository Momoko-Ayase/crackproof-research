---
description: "Senbei 工作区的构建、测试与贡献流程。"
---

# 开发

## 构建

要求 Rust 1.98.1，已在 `rust-toolchain.toml` 中固定。用 `cargo build --release` 构建 CLI；在 Windows 上二进制写到 `target/release/senbei.exe`。

工作区 crate 在 API 保持纯净的范围内是可移植的。浏览器绑定在工作区之外，用 `cargo check --manifest-path senbei-wasm/Cargo.toml` 检查，或用 `wasm-pack` 构建浏览器版。

## 测试

```cmd
cargo test --release --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

纳入版本控制的测试套件在没有受保护样本时也能安全运行。可选的本地 `samples/` 语料由用户管理，被忽略的 `test/` 文件夹可用于真实的 Windows 与 Android 运行。

对 Android 包一次只运行一条命令，因为受保护的 `.so` 可能达数百 MB。APK、APKS、XAPK 测试先读 ZIP 清单，只提取 `.so` 与 `global-metadata.dat` 条目。

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
