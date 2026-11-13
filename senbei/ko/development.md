---
description: "CLI, GUI, WASM 빌드와 코퍼스·퍼징·동치성 테스트, 벤치마크 및 환경 변수."
icon: hammer
---

# 개발

## 빌드

Senbei는 `rust-toolchain.toml`에서 Rust `1.99.1` 버전을 고정합니다. `cargo build --release`는 기본 워크스페이스 멤버인 `senbei-cli`를 빌드하며, 네이티브 데스크톱 워크벤치를 빌드하려면 `-p senbei-gui`를 전달합니다.

{% tabs %}
{% tab title="CLI 및 데스크톱 GUI" %}
```cmd
cargo build --release
cargo build --release -p senbei-gui
cargo build --release --locked -p senbei-cli -p senbei-gui
```

Windows에서는 `target\release\senbei.exe` 및 `target\release\senbei-gui.exe`에 바이너리가 생성됩니다(Linux: `target/release/senbei` 및 `target/release/senbei-gui`).
{% endtab %}

{% tab title="WebAssembly 및 프런트엔드" %}
```cmd
cargo check --workspace --target wasm32-unknown-unknown
cargo check --manifest-path senbei-wasm/Cargo.toml --target wasm32-unknown-unknown
cd senbei-wasm && wasm-pack build --target web --release --out-dir ../web/pkg -- --locked
npm test --prefix web
```

`web/pkg`를 빌드한 뒤 로컬 정적 HTTP 서버로 `web/` 디렉터리를 서빙합니다.
{% endtab %}
{% endtabs %}

## 테스트, 퍼징 및 WASM 동치성 검증

```cmd
cargo test --release --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
```

저장소에 포함된 테스트 스위트는 비공개 샘플 없이도 모두 통과합니다. 로컬 `samples/` 코퍼스가 있으면 Windows 골든 테스트가 모든 fixture에 대해 바이트 단위 일치 여부를 검증합니다(정리 작업 중 `samples/` 디렉터리나 정션 링크를 절대 삭제하지 마십시오).

* **로컬 코퍼스 회귀 테스트 하네스:** 골든 파일을 수정하지 않고 임시 작업 공간에서 매니페스트와 커밋 정보가 연결된 JSON 리포트를 생성합니다.
  ```cmd
  cargo run --release --example corpus_harness -- --emit-manifest samples --manifest-out target/corpus.json
  cargo run --release --example corpus_harness -- --manifest target/corpus.json --report target/corpus-report.json
  ```
* **범위 제한 퍼징 (`fuzz/`):** 6개의 `libFuzzer` 타깃(`pe_detect`, `pe_parse`, `pe_integrity`, `elf_layout`, `metadata_parse`, `metadata_restore`)과 결정론적 `smoke` 러너를 제공합니다.
  ```cmd
  cargo check --manifest-path fuzz/Cargo.toml
  cargo run --release --manifest-path fuzz/Cargo.toml --bin smoke
  ```
  `cargo-fuzz`가 설치된 nightly 툴체인에서는 `fuzz/run.sh [TARGET] [SECONDS]`(기본값: `all`, `60`)로 입력 크기, 실행 시간, 메모리 상한을 적용해 실행할 수 있습니다.
* **네이티브/WASM 바이트 변환 동치성 테스트:** 각 작업을 매번 새로운 Node 워커와 WebAssembly 인스턴스에서 실행하여 결과를 대조합니다.
  ```sh
  cd senbei-wasm && wasm-pack build --target nodejs --release --out-dir ../target/wasm-parity/pkg -- --locked && cd ..
  SENBEI_WASM_PARITY=1 cargo test --release -p senbei-cli --test wasm_parity
  ```
* **엔드투엔드 결정론적 벤치마크:** 지정한 스레드 수별로 워밍업 후 CLI 실행 시간을 측정하며, 엄격한 무결성 검사와 출력 SHA-256 다이제스트 일치 여부를 함께 확인합니다.
  ```cmd
  node scripts/benchmark.mjs target/release/senbei.exe app.exe 3 1,2,4
  node --test scripts/benchmark.test.mjs
  ```

## 환경 변수

| 변수 | 동작 |
| --- | --- |
| `SENBEI_LANG` | CLI 출력 및 GUI 초기 로케일에 적용할 표시 언어 태그 (`en`, `zh-CN`, `zh-TW`, `ja`, `ko`) |
| `SENBEI_THREADS` | 병렬 블록 복구에 사용할 작업자 스레드 상한 (`>= 1`, `1`은 순차 실행이며 `--threads` 플래그가 우선함) |
| `SENBEI_SCAN_ALL` | CLI 폴더 스캔 중 `4,128`바이트 미만의 대상 이름 파일도 프로브 |
| `SENBEI_ANDROID_SAMPLES` | 로컬 Android 샘플 코퍼스 경로 재지정 |
| `SENBEI_REQUIRE_SAMPLES` | `samples/`가 없거나 비어 있을 때 코퍼스 통합 테스트를 건너뛰지 않고 실패 처리 |
| `SENBEI_WASM_PARITY` | `senbei-cli --test wasm_parity` 테스트 활성화 (`1`로 설정 시 실행) |
| `SENBEI_WASM_PKG` / `SENBEI_WASM_PARITY_CORPUS` | Node용 `wasm-pack` 패키지 경로 재지정 / `wasm_parity`에 코퍼스 매니페스트 전달 |
| `SENBEI_NODE` / `SENBEI_WASM_PARITY_TIMEOUT_MS` | Node 실행 파일 경로 재지정 / 작업당 워커 타임아웃(ms) 설정 (기본값 `120000`, `0`은 비활성화) |
| `DD8_SHIFT` / `SEL_DIAG` | PE `.text` `dd8` 시프트 강제 지정(`99`는 건너뜀) 및 레이아웃 선택기 `stderr` 진단 출력용 디버그 변수 (`senbei-gui` 실행 시 경고 배너 표시) |

## 저장소 구조 및 필수 규칙

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

* `senbei-pe`, `senbei-elf`, Windows PE 엔진에는 파일시스템 I/O를 넣지 않아야 하며, `senbei-gui`의 `Workbench` UI는 `wasm32-unknown-unknown` 타깃에서 항상 컴파일 가능해야 합니다.
* 모든 휴리스틱 후보는 시험 복호화 및 검증을 거쳐야 하며, 결정론적 병렬 실행 경로와 순차 실행 경로는 바이트 단위로 동일한 결과를 생성해야 합니다.
* 보호된 바이너리, 복원된 바이너리, 특정 제품을 식별할 수 있는 fixture 이름은 절대 커밋하지 마십시오.
