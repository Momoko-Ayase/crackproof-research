---
description: "네이티브·관리형 툴체인 빌드, 워크스페이스 및 Senbei 1.3.1 오라클 검증과 패키징."
icon: hammer
---

# 개발

## 빌드

빌드에는 Rust `1.98.1` 이상, MASM(`ml` / `ml64`)이 포함된 Visual Studio C++ x86/x64 빌드 도구, Windows 10/11 SDK(MSVC `14.51` 및 SDK `10.0.26100` 환경에서 테스트됨)가 필요합니다. 관리형 패킹과 WPF GUI 빌드에는 .NET 10 SDK와 .NET Framework 4 참조 어셈블리가 추가로 필요합니다.

{% stepper %}
{% step %}
### 네이티브 CLI 및 내장 로더 빌드

`cargo build`는 x86 및 x64용 C/ASM 런타임 로더를 소스 코드에서 함께 컴파일합니다.

```powershell
rustup target add i686-pc-windows-msvc
cargo build --release -p arare-cli
```
{% endstep %}

{% step %}
### 관리형 메타데이터 도구 빌드 (CLR 입력 처리 시 필수)

`tools/managed/build.ps1`은 외부 NuGet 의존성이 없으며(`dotnet.exe`가 기본 경로에 없으면 `-Dotnet <path>` 전달), 실행 시 `Arare.ManagedHost.dll`, `Arare.ManagedHost.runtimeconfig.json`, `Arare.Bootstrap.dll`을 생성합니다.

```powershell
& tools/managed/build.ps1
$env:ARARE_MANAGED_TOOLS = (Resolve-Path target/managed-tools).Path
```

`runtime/` 또는 `tools/managed/` 아래 파일이 변경될 때마다 `tools/managed/build.ps1`을 다시 실행하십시오. 실행 시점에 `arare`와 Python 테스트 하네스는 `ARARE_DOTNET` 환경 변수로 `dotnet.exe`의 절대 경로를 별도 지정하지 않으면 `C:/Program Files/dotnet/dotnet.exe` 경로를 참조합니다.
{% endstep %}

{% step %}
### 릴리스 아카이브 패키징 (선택 사항)

독립 배포판인 `arare-windows-x64` 또는 `arare-windows-x86`(`managed/` 포함, 선택적으로 `Arare.Gui.exe` 포함) 압축본을 구성합니다.

```powershell
& tools/package.ps1 -Architecture x64 -IncludeGui
```
{% endstep %}
{% endstepper %}

## 테스트

{% tabs %}
{% tab title="워크스페이스 검사" %}
표준 워크스페이스 테스트는 자체 생성한 fixture를 사용하므로 Senbei 체크아웃이 필요하지 않습니다.

```powershell
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --workspace --target i686-pc-windows-msvc
```
{% endtab %}

{% tab title="Senbei 1.3.1 오라클" %}
`verification/run_oracle.py`는 패킹된 모든 프로필을 **수정하지 않은 Senbei `1.3.1` 체크아웃**(`version = "=1.3.1"`, `SENBEI_SOURCE`가 더 최신 버전의 Senbei를 가리키면 버전 검사에서 거부됨)으로 정적 언패킹하고 원본, 보호본, 언패킹본 바이너리를 실제로 실행해 검증합니다. 실행 전에 `ARARE_MONO_X86`에 32비트 `mono.exe` 절대 경로를 설정하고, x64 타깃과 x86 타깃은 생성된 아티팩트 경로를 공유하므로 반드시 순차적으로 실행하십시오.

```powershell
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release
python verification/run_oracle.py --senbei-source $env:SENBEI_SOURCE --release --target i686-pc-windows-msvc
```
{% endtab %}

{% tab title="관리형 및 GUI 스위트" %}
ECMA-335 파서/재작성기 테스트, 관리형 도구 탐색 단위 테스트, WPF 스모크 스위트를 실행합니다.

```powershell
python verification/managed/parser_tests.py
cargo test -p arare-engine --lib managed::tool_discovery_tests
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui.SmokeTests -c Release --no-build
```
{% endtab %}
{% endtabs %}

## 기여 규칙

* `arare-pe`, `arare-codec` 및 모든 내장 런타임 코드(`arare-runtime`, `runtime/`)는 항상 `MIT` 라이선스로만 유지하고, `AGPL-3.0-only` 코드를 내장 런타임으로 옮기지 마십시오.
* 상용 도너 바이너리, 추출된 스텁, 실제 보호된 샘플을 저장소에 절대 반입하지 말고 자체 생성한 fixture로만 테스트하십시오.
* 파일 오프셋과 RVA를 별개의 좌표 공간으로 취급하고, 슬라이싱이나 기록 전에 두 좌표를 모두 검증하십시오.
* 비공개 왕복(round-trip) 디코더나 특정 섹션 제외 처리에 의존하지 말고, 모든 포맷 변경 사항을 수정하지 않은 Senbei 정적 복구와 실제 OS 프로세스/DLL 실행으로 검증하십시오.
* 아키텍처 명세는 `docs/design/`, 날짜별 분석 근거와 계획은 `docs/notes/`, 사용자 문서는 이 GitBook 섹션에서 관리합니다. 커밋 메시지에 AI/공동 작성자 출처 트레일러(attribution trailer)를 추가하지 마십시오.
