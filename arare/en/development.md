---
description: "Build, test, and contribution workflow for the Arare workspace."
---

# Development

## Building

Install Rust 1.98.1 or newer, Visual Studio C++ tools for x86/x64 including MASM, and a Windows SDK. Development used MSVC 14.51 and SDK 10.0.26100.

```powershell
rustup target add i686-pc-windows-msvc
cargo build --release -p arare-cli
```

Both native loader architectures are compiled from source during the build. Managed packing additionally needs the .NET 10 SDK/reference pack and .NET Framework 4 reference assemblies:

```powershell
& tools/managed/build.ps1
```

The managed writer has no NuGet dependencies. Create a local binary package after building:

```powershell
& tools/package.ps1 -Architecture x64
```

## Testing

Normal workspace builds do not resolve Senbei. They compile the independent runtime artifacts and use source-generated fixtures:

```powershell
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --workspace --target i686-pc-windows-msvc
```

Keep unchanged `senbei/` as a sibling of `arare/` for the oracle crate:

```powershell
cargo test --manifest-path verification/senbei-oracle/Cargo.toml --release
cargo test --manifest-path verification/senbei-oracle/Cargo.toml --release --target i686-pc-windows-msvc
```

Run the two oracle targets sequentially. Their harnesses share generated artifact locations. Rebuild managed tools after runtime C or C# changes.

GUI smoke tests:

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui.SmokeTests -c Release --no-build
```

A successful private decoder round trip is insufficient. Format integration must pass unmodified Senbei, and runtime claims require actual execution or DLL loading. Never exclude whole sections from comparisons to conceal differences.

## Conventions

- Host tools are AGPL-3.0-only. `arare-codec`, `arare-pe`, and independently written embedded-runtime code are MIT. Do not introduce AGPL implementation code into the embedded runtime.
- Treat Senbei as a reference. Never import a commercial donor executable, extracted stub, opaque profile, or protected application into the repository.
- Public tests use generated fixtures. Existing sample directories outside the repository are user-managed.
- PE file offsets and RVAs are distinct. Validate both before reading, copying, allocating, or writing.
- Keep Android and IL2CPP metadata obfuscation out of the current implementation.
- Do not add attribution trailers to commits.

Living contracts live under `docs/design/`. Dated reviews and implementation plans live under `docs/notes/`. Operator documentation is this GitBook section.
