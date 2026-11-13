---
description: "배치 arare protect 및 verify 작업을 구성·실행하는 WPF 프런트엔드."
icon: window-maximize
---

# GUI

`Arare.Gui.exe`는 작업 대기열을 바탕으로 `arare protect` 명령줄을 조합하고, 실제 실행할 CLI 명령어를 미리 보여주며, 순차 패킹과 패킹 후 선택적 디코딩 검증을 실행하는 Windows Presentation Foundation (WPF) 데스크톱 프런트엔드입니다.

## 빌드 및 실행

빌드에는 .NET 10 SDK가 필요하며, 패키징된 GUI 빌드를 실행하려면 일치하는 .NET 10 Desktop Runtime이 필요합니다.

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui -c Release
```

`Arare.Gui.exe`를 `arare.exe`와 같은 폴더에 두거나 `arare.exe`를 `PATH`에 등록하십시오. 다른 바이너리를 지정하려면 하단 상태 표시줄에서 **Locate…**를 선택합니다. 실행 시 명령줄 인자로 파일과 폴더를 전달해 초기 목록을 채울 수도 있습니다.

```powershell
Arare.Gui.exe app.exe game_folder\
```

* **폴더 선택기:** 하위 폴더 재귀 옵션을 끄면 선택한 폴더와 최대 3단계 깊이까지의 `Managed` 및 `Plugins` 하위 디렉터리만 스캔하며, 하위 폴더 재귀를 켜면 전체 디렉터리 트리를 순회합니다.
* **위치 인자 폴더:** 저장된 하위 폴더 체크박스 상태와 관계없이 항상 비재귀 스캔(`root` 및 최대 깊이 3까지의 `Managed`/`Plugins`)을 수행합니다.

## 대기열, 행별 재정의 및 검증

* **행별 프로필 제안:** PE 헤더를 분석해 적합한 프로필을 자동으로 제안합니다(`x86` -> `pe32`, `x64` -> `pe64-modern`, `AnyCPU` 관리형 -> `pe32`, `legacy-dll`은 64비트 DLL로만 제한).
* **출력 경로 및 충돌 검사:** 출력 경로는 기본적으로 각 입력 옆의 `.\arare-protected\`(또는 지정한 단일 폴더)로 설정됩니다. 출력 경로가 중복되거나 출력 파일(`._` 컴패니언 파일 포함)이 대기열의 입력 파일을 덮어쓰게 되는 경우에는 **Replace existing outputs**가 체크되어 있더라도 실행 전에 차단됩니다.
* **유효 옵션 상태 표시:** 환경 검사, 페이지 암호화, `scribble`, **ErrLog** 메일슬롯 리포트(`--errlog`) 체크박스는 선택된 모듈 유형에 대한 실제 유효 기본값(`disk-integrity`가 `clean-code`를 대체하는 규칙 포함)을 표시하며, 행별로 재정의된 항목을 구분해 보여주고 원클릭 초기화 버튼을 제공합니다. `--antidebug-av`는 GUI에 노출되지 않으며 CLI의 모듈별 기본값(EXE는 `on`, DLL은 `off`)을 그대로 따릅니다.
* **스크립트 내보내기 및 실행:** **Copy as .ps1** 버튼을 누르면 출력 디렉터리를 생성하고 `arare protect`(및 선택적 `arare verify`)를 실행하며 종료 코드가 0이 아닐 때 중단하는 PowerShell 스크립트를 그대로 내보냅니다. **Protect 1 file** / **Protect N files**는 대기열을 순차적으로 실행하며, **Cancel**은 현재 처리 중인 항목을 마친 뒤 실행을 멈춥니다.
* **단독 검증:** **Verify existing…**은 이미 보호된 파일을 직접 실행하지 않고 후보 프로필별로 `arare verify`를 수행합니다. **Check encoding after protect**를 켜면 각 보호 작업 직후 `arare verify`를 자동으로 실행합니다.
* **설정 저장:** UI 환경 설정은 실행 파일 옆의 `Arare.Gui.settings.json`에 저장되며, 작업 대기열 자체는 현재 세션에서만 유지됩니다.

## 스모크 테스트

```powershell
dotnet run --project gui/Arare.Gui.SmokeTests -c Release
```

이 테스트 스위트는 PE 분류, CLI 인자 생성, 모듈별 기본값 및 재정의 해석, `.ps1` 스크립트 생성, 경로 충돌 검증, 모의(mock) 백엔드 기반 보호/검증 상태 전환, 실행 중 창 닫기 확인, 폴더 스캔 깊이 규칙, 설정 저장을 검증합니다. 라이선스는 `AGPL-3.0-only`입니다.
