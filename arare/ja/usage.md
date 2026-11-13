---
description: "protect・inspect・verify コマンド、プロファイル、環境チェック、ページ暗号化。"
icon: terminal
---

# 使い方

`arare-cli` をビルドすると `target/release/arare.exe` が生成されます（Senbei のチェックアウトは不要です）。マネージドアセンブリを保護する場合は、これに加えて .NET 10 ランタイムと3つのマネージドツールファイル（`Arare.ManagedHost.dll`、`Arare.ManagedHost.runtimeconfig.json`、`Arare.Bootstrap.dll`）を `arare.exe` と同じ場所の `managed/` に配置するか、`ARARE_MANAGED_TOOLS` で指定する必要があります（[開発](development.md)を参照）。GUI によるバッチ処理については [GUI](gui.md) を参照してください。

```text
arare protect INPUT -o|--output OUTPUT --profile PROFILE
    [--seed 64_HEX_DIGITS] [--no-compression]
    [--storage embedded|companion] [--check NAME=on|off]...
    [--page-encrypt on|off] [--scribble on|off]
    [--errlog on|off] [--antidebug-av on|off]
    [--force] [--json]

arare inspect INPUT [--json]

arare verify INPUT --profile PROFILE [--companion PATH] [--json]
```

## プロファイルと格納方式

| プロファイル | 対象のレイアウト系統 |
| --- | --- |
| `pe32` | PE32 x86 ネイティブイメージ、および対応する x86 / AnyCPU マネージドアセンブリ |
| `pe64-classic` | マーカーベースの従来型 EXE スタイル PE32+ x64 EXE および DLL |
| `pe64-modern` | マーカーなしの EXE スタイル PE32+ x64 EXE および DLL |
| `legacy-dll` | 旧式の専用 PE32+ x64 DLL レイアウト（埋め込み格納のみ対応） |

プロファイル名は商用製品のバージョンではなく構造上のレイアウト系統を表します。入力ファイルに対する制約は[対応範囲](support.md)を参照してください。

* **コンパニオン格納（`--storage companion`）:** `OUTPUT`（4 KiB のヘッダー／オーバーレイスタブ）と `<OUTPUT>._`（暗号化ペイロード、`0x1000..0x1020` の 32 バイトヘッダーで照合）の両方を書き出します。2つのファイルは同じフォルダーに配置してください。
* **シードと圧縮:** `--seed` を省略すると Windows の CSPRNG からランダムな 32 バイトを取得し、16進シード値を出力します。`--no-compression` を指定すると、ローダーステージの符号化は維持したまま、アプリケーションセクションのブロックを非圧縮で格納します。
* **静的検証（`verify`）:** ターゲットを実行することなく、Arare 独自のネイティブデコーダーで保護済みファイルを復号検証します。`--companion` 省略時でも、`<INPUT>._` の 32 バイトヘッダーが一致すれば自動でペアリングされます。

## 環境チェックと失敗時の応答

保護されたモジュールは起動時の3つのフェーズ（ファイル展開前の Phase 1、展開後の Phase 2、ページ保護処理後の Phase 3）で構成可能なチェックを実行します。既定値を変更するには `--check NAME=on|off` を複数回指定します。

| モジュール種別 | 既定で有効なチェック |
| --- | --- |
| ネイティブ EXE | `antidebug`, `crc-loader`, `debug-port`, `os-version`, `boot-options`, `vm-registry`, `injected-dll`, `injected-thread`, `clean-code` |
| ネイティブ DLL | `crc-loader`, `vm-registry`, `host-process` |
| マネージド EXE | `crc-loader`, `vm-registry` |
| マネージド DLL | `crc-loader`, `vm-registry`, `host-process` |

ネイティブ・マネージドの両 DLL では `host-process` が既定で `on` になっているため、保護されていないホストプロセスから保護済み DLL をロードする場合は `--check host-process=off` を指定してください。`vm-backdoor`、`parent-process`、`hyperv-guest` はすべてのモジュール種別で既定値が `off` です。

| CLI チェック名 | ステージコード | 動作 |
| --- | --- | --- |
| `antidebug` | `410` | 7サブステージ：`IsDebuggerPresent`、`PEB.BeingDebugged`、`PEB.NtGlobalFlag & 0x70`、ハードウェアデバッグレジスター `DR0`..`DR3` / `DR7 & 0xFF`（`GetThreadContext`）、および `NtQueryInformationProcess`（`ProcessDebugPort`、`ProcessDebugFlags == 0`、`ProcessDebugObjectHandle`） |
| `crc-loader` | `510` | ローダーコードの CRC-32 自己整合性チェック |
| `debug-port` | `520` | カーネルデバッグポートの照会 |
| `kernel-debugger` | `52F` | `KdDebuggerEnabled` およびシステムカーネルデバッガーの検出 |
| `vm-backdoor` | `540` | VMware `0x5658` I/O ポートのプローブ（汎用 CPUID ハイパーバイザービットは無視し、Hyper-V / VBS を許可） |
| `hyperv-guest` | `541` | Arare 独自の Hyper-V ゲストパーティション特権チェック（`Hv#1` CPUID） |
| `parent-process` | `A03` | `explorer.exe` または `cmd.exe` 以外の親プロセスを拒否 |
| `os-version` | `C00` | Windows 10 ビルド `10240` 以降を要求 |
| `boot-options` | `C01` | テスト署名およびデバッグブートフラグを拒否 |
| `msc-log` | `BD0` | `C:\Windows\msc.log.log` が存在する場合に拒否 |
| `os-compat` | `B00` | OS 互換性ゲート |
| `vm-registry` | `A09` | システムハードウェア／BIOS の VM レジストリマーカー検査（`Hv#1` が Hyper-V / VBS を示す場合は汎用的な `Virtual` / `VRTUAL` / `Microsoft Hyper-V` を許可） |
| `injected-dll` | `A0F` | OEP 到達前にロード済みモジュールを走査 |
| `injected-thread` | `A07` / `A01` | 想定外の外部スレッドを検出 |
| `host-process` | `A11` | 互換性のある Arare 保護済みホスト EXE（`.arldr` または `.armclr` マーカー）を要求 |
| `host-stamp` | `A11` | `host-process=on` 時にホスト・DLL 間の実行時コンテキストスタンプを追加検証 |
| `clean-code` | `A08` | 未改変のシステム DLL バイト列を経由してローダー呼び出しを実行 |
| `disk-integrity` | `A04` | `clean-code` を置き換え（同時指定時もこちらが優先）、マップ済みシステム DLL とディスク上のイメージの比較も実施 |
| `legacy-debugger` | `BE0` | レガシーデバッガーデバイスのプローブ |
| `openark-device` | `E55` | Phase 3（ページ保護処理後）の OpenArk ドライバーデバイス検査 |
| `cheat-engine-device` | `E91` | Phase 3（ページ保護処理後）の Cheat Engine ドライバーデバイス検査 |

{% hint style="warning" %}
**明確な用途がない限り `hyperv-guest` は有効化しないでください。** `--check hyperv-guest=on` はルート／ホスト側の VBS パーティションを許可しつつ、`Hv#1` CPUID パーティション特権で識別されるゲスト VM を拒否します。ハイパーバイザーの CPUID リーフはマスクや偽装が可能であるため、`hyperv-guest` は耐タンパー機構ではなく実行環境の制限用オプションとして扱ってください。
{% endhint %}

**チェック失敗時の応答（`--antidebug-av`）:** `--antidebug-av` の既定値は EXE で `on`、DLL で `off` です（ネイティブモジュールのログには `-AV=ON` / `-AV=OFF` と記録されます）。`--antidebug-av=on` のネイティブモジュールでチェックに失敗すると、ランタイムはログを閉じた後、アタッチ中のデバッガーを即座にブレークさせるため `RaiseException(0xC0000005)`（`EXCEPTION_ACCESS_VIOLATION`）の送出と null アドレスへの書き込みを行い、最後に `TerminateProcess(0xE0A00000 | substage)` を呼び出します。`--antidebug-av=off` のネイティブモジュールおよびマネージドモジュールは直接 `TerminateProcess` を呼び出します。

## ページ暗号化

`--page-encrypt` の既定値は EXE で `on`、DLL で `off` です。セクション再構築後、ランタイムは実行可能なアプリケーションページをインプレースで再暗号化して `PAGE_NOACCESS` に設定し、`ntdll!KiUserExceptionDispatcher` を hook して初回実行時のアクセス違反例外でページをオンデマンド復号します。ページ暗号化が有効な場合、書き込みかつ実行可能な（`RWX`）セクションや `0x1000` 未満のセクションアライメントを持つ入力は拒否されます。

`--scribble=on`（既定値 `off`、`--page-encrypt=on` が必須）を指定すると、すでに復号されてメモリ上にあるページの一部バイト列をアクセス違反例外の合間にマスクします。

## デバッグログと `ErrLog-Pec`

`protect --json`（および標準コンソール出力）は、モジュール固有の12桁16進数 `log_folder` を出力します。`%TEMP%\<log_folder>` が存在し、かつ作成から 48 時間以内である場合、モジュールは実行時ステータスログ（EXE は `HHMMSSmmmE-...`、DLL は `HHMMSSmmmD-...`）を書き出し、末尾に `AAA-BBB-CCC` の終了サマリーを記録します。

{% hint style="info" %}
**DLL におけるログゲートの継承:** 保護された Arare EXE のプロセス内に保護された DLL がロードされると、シードが異なる場合や `host-process=off` が設定されている場合でも、常に EXE 側のロギングコンテキストが DLL に適用されます。EXE 側の `%TEMP%` フォルダーが存在しないか 48 時間を超えている場合、DLL 自身のフォールバック用 `log_folder` の有無にかかわらず DLL はログを出力しません。
{% endhint %}

`--errlog=on`（既定値 `off`）を指定すると、`%TEMP%` フォルダーのゲート条件とは独立して、終了時に診断パケットを `\\.\mailslot\ErrLog-Pec<suffix>`（`<suffix>` は `((key + 1) * 0x3039) % 0x8003` から算出される4桁の16進数）へ送信します。パケットにはタイムスタンプ、`AAA-BBB-CCC` コード、およびモジュール／OS 情報が含まれます。

## 出力の書き込みと JSON レポート

出力イメージはメモリ上で最後まで符号化してから一時ファイルへ書き出してフラッシュし、アトミックにリネームして配置します（既存ファイルの上書きには `--force` が必要です）。入力ファイルのシンボリックリンクや正規化パス上の別名への出力は拒否されます。別個のハードリンクエントリを置き換えた場合は、元の入力ファイルのバイト列はそのまま維持されます。

<details>
<summary>JSON 出力フィールド（protect、inspect、verify）</summary>

* **`protect --json`:** `output`, `profile`, `storage`, `architecture`, `module`, `input_size`, `output_size`, `seed`, `normalizations`, `log_folder`, `companion`, `companion_size`.
* **`inspect --json`:** `architecture`, `module`, `entry_point`, `image_base`, `image_size`, `file_size`, `sections`（`name`, `rva`, `virtual_size`, `raw_offset`, `raw_size`, `characteristics`）.
* **`verify --json`:** `valid`, `profile`, `companion`, `image_size`, `recovered_file_size`, `entry_point`.
</details>
