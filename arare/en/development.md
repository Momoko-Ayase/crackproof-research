---
description: "Build native and managed toolchains, run workspace and Senbei 1.3.1 oracle suites, and package releases."
icon: hammer
---

# Development

## Building

Prerequisites: Rust `1.98.1` or newer, Visual Studio C++ x86/x64 build tools with MASM (`ml` / `ml64`), and the Windows 10/11 SDK (tested with MSVC `14.51` and SDK `10.0.26100`). Managed packing and the WPF GUI additionally require the .NET 10 SDK and .NET Framework 4 reference assemblies.

{% stepper %}
{% step %}
### Build the native CLI and embedded loaders

`cargo build` compiles both x86 and x64 C/ASM runtime loaders from source:

```powershell
rustup target add i686-pc-windows-msvc
cargo build --release -p arare-cli
```
{% endstep %}

{% step %}
### Build the managed metadata tools (required for CLR inputs)

`tools/managed/build.ps1` has zero NuGet dependencies (pass `-Dotnet <path>` if `dotnet.exe` is not in its default location) and emits `Arare.ManagedHost.dll`, `Arare.ManagedHost.runtimeconfig.json`, and `Arare.Bootstrap.dll`:

```powershell
& tools/managed/build.ps1
$env:ARARE_MANAGED_TOOLS = (Resolve-Path target/managed-tools).Path
```

Re-run `tools/managed/build.ps1` whenever files under `runtime/` or `tools/managed/` change. At runtime, `arare` and the Python test harnesses look for `dotnet.exe` at `C:/Program Files/dotnet/dotnet.exe` unless `ARARE_DOTNET` specifies an absolute `dotnet.exe` path.
{% endstep %}

{% step %}
### Package a release archive (optional)

Assemble the standalone `arare-windows-x64` or `arare-windows-x86` distribution (including `managed/` and optionally `Arare.Gui.exe`):

```powershell
& tools/package.ps1 -Architecture x64 -IncludeGui
```
{% endstep %}
{% endstepper %}

## Testing

{% tabs %}
{% tab title="Workspace checks" %}
Standard workspace tests use generated fixtures and never require a Senbei checkout:

```powershell
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --workspace --target i686-pc-windows-msvc
```
{% endtab %}

{% tab title="Senbei 1.3.1 oracle" %}
`verification/run_oracle.py` verifies every packed profile against an **unchanged Senbei `1.3.1` checkout** (`version = "=1.3.1"`; pointing `SENBEI_SOURCE` at a newer Senbei version is rejected by the version check) plus live execution of original, protected, and unpacked binaries. Set `ARARE_MONO_X86` to an absolute 32-bit `mono.exe` path before running, and execute the x64 and x86 targets sequentially because they share generated artifact paths:

```powershell
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release --target i686-pc-windows-msvc
```
{% endtab %}

{% tab title="Managed & GUI suites" %}
Run the ECMA-335 parser/rewriter tests, managed tool-discovery unit tests, and WPF smoke suite:

```powershell
python verification/managed/parser_tests.py
cargo test -p arare-engine --lib managed::tool_discovery_tests
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui.SmokeTests -c Release --no-build
```
{% endtab %}
{% endtabs %}

## Contributor rules

* Keep `arare-pe`, `arare-codec`, and all embedded runtime code (`arare-runtime`, `runtime/`) `MIT`-clean; never move `AGPL-3.0-only` code into the embedded runtime.
* Never import commercial donor binaries, extracted stubs, or real protected samples into the repository; test exclusively with generated fixtures.
* Treat file offsets and RVAs as distinct coordinate spaces and validate both before slicing or writing.
* Verify every format change against unchanged Senbei recovery and real OS process/DLL execution rather than private round-trip decoders or section exclusions.
* Keep architecture specs in `docs/design/`, dated evidence and plans in `docs/notes/`, and user-facing documentation in this GitBook section. Do not add attribution trailers to commits.
