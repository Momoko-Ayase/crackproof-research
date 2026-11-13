---
description: "CLI 명령어, 검사 리포트, 폴더 및 APK 처리, 표시 언어, 플래그 및 종료 코드."
icon: terminal
---

# 사용법

```text
senbei [inspect|unpack] <file|folder> [--out DIR] [-v|--verbose] [-q|--quiet]...
    [--json] [--dry-run] [--threads N] [--color auto|always|never] [--scan-all]
    [--strict-integrity] [--max-entry-mib N] [--max-total-mib N]
    [--max-entries N] [--max-depth N] [--no-log] [--no-pause]
    [-V|--version] [-h|--help]
```

`senbei <path>`는 `senbei unpack <path>`와 동일합니다. `inspect`와 `unpack`은 `<file|folder>` 앞에 위치할 때 서브커맨드로 파싱됩니다(이름이 `inspect`인 파일이나 폴더를 대상으로 지정하려면 `./inspect` 또는 `.\inspect`를 전달하십시오).

## 주요 사용 패턴

{% tabs %}
{% tab title="언패킹" %}
복원된 파일은 확장자 앞에 `.unpack`을 붙여 `<parent>/unpack/`(파일 입력) 또는 `<root>/unpack/`(폴더 입력) 아래에 저장되며, `--out DIR` 옵션을 지정하면 복원 파일과 실행 로그를 모두 해당 디렉터리에 저장합니다.

```cmd
senbei app.exe
senbei app.exe --out C:\out
senbei game.apk --out C:\out
senbei "C:\Games\SampleTitle"
```

`global-metadata.dat` 파일의 경우 메서드 토큰이나 인덱스가 실제로 변경될 때만 `global-metadata.unpack.dat` 파일을 생성합니다. 이미 정규화된 파일이나 지원하지 않는 버전은 폴더 실행 시 건너뛰며, 단일 파일을 직접 언패킹할 때는 오류로 보고합니다.
{% endtab %}

{% tab title="검사 및 JSON" %}
`inspect`는 출력 파일이나 실행 로그를 저장하지 않고 메모리상에서 전체 정적 복구를 수행하여 분석 근거를 수집하며, 대상 바이너리는 실행하지 않습니다.

```cmd
senbei inspect module.dll
senbei inspect module.dll --json
senbei inspect module.dll --strict-integrity --json
```

리포트에는 원본 해시, 파싱된 PE/ELF/메타데이터 헤더, 복호화된 보호 테이블, 시도한 모든 복구 경로와 기각 사유, 최종 선택된 경로, 탐색된 단계 파라미터(물리 파일 오프셋, 컴패니언 결합 오프셋, 작업 이미지 RVA 구분), 정적 검증 결과가 포함됩니다.
{% endtab %}

{% tab title="시험 실행 및 CI" %}
`--dry-run`은 출력 파일이나 로그를 저장하지 않고(`inspect` 트레이스도 수집하지 않음) 복구와 정적 검증만 수행합니다. 임시 Android 추출 작업 공간은 종료 시 자동으로 정리됩니다.

```cmd
senbei unpack module.dll --dry-run
senbei unpack module.dll --dry-run --json --strict-integrity
senbei unpack folder --strict-integrity --no-pause -q
```

`inspect`와 `--dry-run`은 모두 `--out` 옵션과 함께 사용할 수 없습니다.
{% endtab %}
{% endtabs %}

## Android 라이브러리 및 패키지

Senbei는 보호된 AArch64 `.so` 바이너리(`libil2cpp.unpack.so` 또는 `<stem>.unpack.so`)를 복원하며 `.apk`, `.apks`, `.xapk` 패키지를 직접 처리합니다.

1. ZIP 센트럴 디렉터리를 먼저 읽고, `.apks`/`.xapk` 번들 내부의 중첩 `.apk` 항목을 `--max-depth` 깊이까지 추적합니다.
2. 설정된 `--max-entry-mib`, `--max-total-mib`, `--max-entries` 한도 내에서 `.so` 항목과 파일명이 정확히 `global-metadata.dat`인 항목만 임시 파일로 스트리밍합니다.
3. 외부 `v24.1` 메타데이터를 동일 앱의 모듈 `0x0C`와 짝지어 복원하고(분할 APK 간 `AndroidManifest.xml` 패키지명 + 버전 기준, 또는 `<root>/lib/<abi>/` + `<root>/assets/` 기준), 경량 `v24` XOR 데이터를 `global-metadata.unpack.dat` 파일로 복원하며, 패키지 내부 항목과 동일한 개별 파일은 중복 처리하지 않습니다.

## 폴더 스캔 및 컴패니언 파일

폴더 모드는 하위 디렉터리를 재귀적으로 순회하되, `unpack` 디렉터리(대소문자 구분 없음, 단 루트 대상 자체가 `unpack`인 경우는 예외)와 루트 아래의 NTFS 리파스 포인트(reparse point) 하위 디렉터리는 건너뜁니다.

* **스캔 대상 이름 (대소문자 구분 없음):** `.exe`, `.dll`, `.so`, `global-metadata.dat`, `.apk`, `.apks`, `.xapk` 파일을 대상으로 합니다. 매니페스트 패키지명과 버전이 같은 동일 폴더의 분할 `.apk` 파일은 자동으로 그룹화합니다. `--scan-all`(또는 `SENBEI_SCAN_ALL`)을 지정하지 않으면 `4,128`바이트 미만의 후보 파일은 열지 않고 건너뜁니다.
* **Windows `._` 컴패니언 파일:** 같은 경로에 있는 `.exe._` 및 `.dll._` 파일은 건너뛴 파일로 집계되지 않고 대응하는 스텁 파일과 결합되어 처리됩니다. 관리형 컴패니언 DLL은 복호화된 IL 메서드 본문 위에 스텁의 `COR20` 테이블을 덮어써야 하므로 `Module.dll`과 `Module.dll._` 파일이 모두 필요합니다.

{% hint style="info" %}
**컴패니언 진단 메시지.** `Missing companion file`은 PE32+ 엔트리 레코드에 `._` 컴패니언 선언(`~0x1000` 및 `~"._\0\0"`)이 명시되어 있는데 `<input>._` 파일이 없을 때만 보고됩니다. `Companion doesn't match`는 `<input>._` 파일이 32바이트 미만이거나 `0x00..0x20` 헤더가 `stub[0x1000..0x1020]` 값과 일치하지 않음을 의미합니다.
{% endhint %}

## 표시 언어 및 터미널 색상

Senbei는 `en`(영어), `zh-CN`(중국어 간체), `zh-TW`(중국어 번체), `ja`(일본어), `ko`(한국어)의 5개 표시 언어를 지원합니다.

{% tabs %}
{% tab title="명령 프롬프트" %}
```cmd
set SENBEI_LANG=ja
senbei inspect module.dll
```
{% endtab %}

{% tab title="PowerShell" %}
```powershell
$env:SENBEI_LANG = "zh-TW"
senbei inspect module.dll
```
{% endtab %}

{% tab title="POSIX / Bash" %}
```sh
SENBEI_LANG=ko senbei inspect module.dll
```
{% endtab %}
{% endtabs %}

* **로케일 결정 순서:** `SENBEI_LANG`은 `.encoding` 및 `@modifier` 접미사를 제거하고 `-` 또는 `_` 구분자를 대소문자 구분 없이 매칭하며, 지역 코드보다 문자 체계 서브태그(`Hans` / `Hant`)를 우선합니다(`zh-Hans-HK` -> 중국어 간체, `zh-Hant` / `zh-TW` / `zh-HK` / `zh-MO` -> 중국어 번체). `SENBEI_LANG`이 설정되지 않은 경우 Windows UI 언어 목록 또는 `LC_ALL` / `LC_MESSAGES` / `LANG` / `LANGUAGE`를 확인하며, 일치하는 항목이 없으면 영어로 표시합니다.
* **영어로 고정되는 출력:** `--json` 출력, 저장된 `.log` 파일, `inspect` 구조 근거 테이블, `-v` 단계별 상세 줄은 항상 영어로 유지됩니다. 번역된 오류 메시지가 내부 상세 오류를 요약한 것일 때는 다음 줄에 영어 원문 상세 내용을 함께 출력합니다.
* **색상 제어 (`--color MODE` 또는 `--color=MODE`):** 기본값인 `auto`는 스트림별 TTY 여부를 확인하고 `NO_COLOR`가 비어 있지 않거나 `TERM=dumb`이면 색상을 끕니다. `always`는 사람이 읽는 터미널 출력에 ANSI 색상을 강제 적용하며, `never`는 색상을 비활성화합니다. `--json` 출력과 `.log` 파일에는 ANSI 이스케이프 시퀀스가 절대 포함되지 않습니다.

## 정적 검증 및 브라우저 제한

정적 검증 단계에서는 복원된 PE 헤더, 섹션 매핑, 엔트리 포인트 도달 가능성 및 CRT 분기 대상, 최대 256개의 임포트 디스크립터, 네이티브 데이터 디렉터리, CLR `BSJB` 스트림을 검사하며, Android ELF의 `PT_LOAD` 범위, 동적 테이블, 심볼 해시, 재배치, 생성자 포인터도 함께 검증합니다. 구조 경고나 치명적이지 않은 오류가 있는 결과물도 `unpack` 실행 시 파일로 기록되며 `suspect`로 집계됩니다. `--strict-integrity` 플래그를 지정하면 `unpack`, `--dry-run`, `inspect` 실행 중 `suspect` 결과가 하나라도 발생했을 때 종료 코드 `1`로 종료합니다.

WebAssembly 브라우저 앱에서는 **Input limit per module (MiB)** 기본값이 `256`(`8`..`4096` MiB 범위, 메모리에 읽기 전에 스텁과 `._` 컴패니언 크기를 합산)이며, **Export JSON**을 누르면 로컬 `senbei.browser-report` v1 파일을 다운로드합니다. Android `.so` 및 앱 패키지 복원에는 네이티브 `senbei` 또는 `senbei-gui`를 사용해야 합니다.

## 플래그 레퍼런스

| 플래그 | 동작 |
| --- | --- |
| `--out DIR` | 언패킹된 파일과 실행 로그를 `DIR` 아래에 기록합니다 (`unpack` 모드 전용). |
| `--dry-run` | 출력 파일이나 로그를 저장하지 않고 복구 및 정적 검증만 수행합니다. |
| `--json` | `stdout`으로 버전이 명시된 JSON 리포트를 출력합니다 (`-q -q` 지정 시에도 출력되며 실행 로그 저장과 종료 대기를 비활성화함). |
| `--threads N` | 작업자 스레드 상한(`N >= 1`)을 지정하며 `SENBEI_THREADS`보다 우선합니다 (`1`은 순차 실행). |
| `--color auto\|always\|never` | ANSI 터미널 색상을 제어합니다 (`--color=MODE` 형식도 허용). |
| `-v`, `--verbose` | 단계별 진행 상태 줄을 출력합니다. |
| `-q`, `--quiet` | 배너와 파일별 진행 출력을 숨깁니다. `-q -q`처럼 개별 플래그로 두 번 전달하면 모든 `stdout`과 런타임 `stderr` 출력을 끕니다. |
| `--no-log` | `senbei-YYYYMMDD-HHMMSS.log` 파일 기록을 건너뜁니다. |
| `--scan-all` | 폴더 스캔 중 `4,128`바이트 미만의 대상 이름 파일도 프로브합니다. |
| `--strict-integrity` | 복원된 이미지 중 `suspect` 판정이 있으면 종료 코드 `1`로 종료합니다 (`unpack`, `--dry-run`, `inspect` 모두 적용). |
| `--max-entry-mib N` | 단일 Android ZIP 항목, 디코딩된 컨테이너, 아티팩트 또는 출력 파일의 최대 크기(MiB, `N >= 1`, 기본값 `2048`). |
| `--max-total-mib N` | Android 아카이브 추출 및 작업당 복구의 누적 처리 한도(MiB, `N >= 1`, 기본값 `8192`). |
| `--max-entries N` | 중첩 Android 아카이브 전체의 아카이브 항목 수 및 Stage 2 레코드 최대 수(`N >= 1`, 기본값 `100000`). |
| `--max-depth N` | 중첩 Android APK 및 Stage 2 스트림의 최대 중첩 깊이(`0` 허용, 기본값 `32`). |
| `--no-pause` | Windows 탐색기에서 실행했을 때 표시되는 종료 전 대기 프롬프트를 건너뜁니다. |
| `-V`, `--version` / `-h`, `--help` | 버전 또는 사용법 도움말을 출력하고 종료 코드 `0`으로 종료합니다. |

## 종료 코드

| 코드 | 의미 |
| --- | --- |
| `0` | 명령 성공 (`unpack`, `--dry-run`, `inspect`, `--help` 또는 `--version`). 대상 오류가 없으며, `--strict-integrity` 지정 시 `suspect` 결과물도 없는 상태입니다. |
| `1` | 하나 이상의 대상 복구 실패, 스캔/파일 프로브 읽기 실패, Android 리소스 제한 초과, 또는 `--strict-integrity` 사용 시 `suspect` 이미지가 발견된 상태입니다. |
| `2` | 잘못된 명령줄 인자 (인자 없이 `senbei` 실행, 호환되지 않는 플래그 조합, 유효하지 않은 숫자 제한값 포함). |
