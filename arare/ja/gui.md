---
description: "バッチ protect・verify ジョブの作成、プレビュー、順次実行を行う WPF フロントエンド。"
icon: window-maximize
---

# GUI

`Arare.Gui.exe` は Windows Presentation Foundation（WPF）製のフロントエンドです。ジョブキューから `arare protect` のコマンドラインを組み立て、実際に渡される CLI 引数をプレビューしたうえで、保護処理と保護後の復号検証（任意）を順次実行します。

## ビルドと起動

ビルドには .NET 10 SDK が必要です。パッケージ済みの GUI バイナリを実行するには対応する .NET 10 Desktop Runtime が必要です。

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui -c Release
```

`Arare.Gui.exe` を `arare.exe` と同じフォルダーに配置するか（または `arare.exe` を `PATH` に通すか）、ステータスバーの **Locate…** から別のバイナリを選択してください。起動時引数でファイルやフォルダーをあらかじめキューに追加することもできます。

```powershell
Arare.Gui.exe app.exe game_folder\
```

* **フォルダー選択:** サブフォルダー再帰がオフの場合は、選択したフォルダー直下および深さ3階層までの `Managed` または `Plugins` サブディレクトリを走査します。サブフォルダー再帰をオンにするとディレクトリツリー全体を走査します。
* **起動時引数でのフォルダー指定:** 保存されているサブフォルダー設定のチェック状態にかかわらず、常に非再帰走査（ルート直下および深さ3階層までの `Managed`/`Plugins`）が適用されます。

## キュー管理・個別上書き・検証

* **行単位のプロファイル提案:** PE ヘッダーから自動的に初期値が選択されます（`x86` -> `pe32`、`x64` -> `pe64-modern`、`AnyCPU` マネージド -> `pe32`。`legacy-dll` は 64ビット DLL に限定されます）。
* **出力パスと衝突検査:** 既定の出力先は各入力ファイルと同じ場所の `.\arare-protected\`（または指定した単一フォルダー）です。出力パスの重複や、キュー内の入力ファイルを上書きしてしまう出力先（`._` コンパニオンを含む）は、**Replace existing outputs** にチェックが入っている場合でも実行前にブロックされます。
* **有効状態の可視化:** 環境チェック、ページ暗号化、scribble、および **ErrLog** メールスロット通知（`--errlog`）の各チェックボックスには、選択中のモジュール種別に対する実効既定値（`disk-integrity` による `clean-code` の置き換えを含む）が表示されます。行単位の上書き箇所は明示され、ワンクリックで初期状態へリセットできます。`--antidebug-av` は GUI には設定項目がなく、CLI のモジュール種別ごとの既定値（EXE は `on`、DLL は `off`）に従います。
* **スクリプト出力と実行:** **Copy as .ps1** は、出力ディレクトリの作成、`arare protect`（および任意の `arare verify`）の実行、非ゼロ終了コード時の停止処理を含む PowerShell スクリプトをそのままコピーします。**Protect 1 file** / **Protect N files** でキューを順次実行し、**Cancel** を押すと現在処理中の項目が完了した時点で停止します。
* **単体検証:** **Verify existing…** は保護済みファイルを起動せずに候補プロファイルに対して `arare verify` を実行します。**Check encoding after protect** を有効にすると、各保護ジョブの完了後に `arare verify` が自動実行されます。
* **設定の保存:** UI 設定は実行ファイルと同じ場所の `Arare.Gui.settings.json` に保存されます。ジョブキュー自体はセッション中のみ保持されます。

## スモークテスト

```powershell
dotnet run --project gui/Arare.Gui.SmokeTests -c Release
```

テストスイートは PE 分類、CLI 引数生成、モジュール種別ごとの既定値／上書き解決、`.ps1` スクリプト生成、パス衝突検証、モックバックエンドに対する protect/verify の状態遷移、実行中のウィンドウ終了確認、フォルダー走査の階層ルール、および設定ファイルの保存・読み込みを検証します。ライセンスは `AGPL-3.0-only` です。
