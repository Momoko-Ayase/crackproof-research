---
description: "デバッガ、VM、システム整合性、注入 DLL・スレッド、A11/A15 ホスト検証、アンフック検査"
icon: user-shield
---

# 実行環境・耐解析チェック

CrackProof の起動時チェックは、ペイロード展開前の Phase 1、`C`/`B`/`A` シーケンサの各パス、およびページ保護設定後に任意実行される `E` 系チェックにまたがって構成されています。

{% tabs %}
{% tab title="デバッガ検知" %}
* **`410`（ユーザーモード耐デバッグ）:** `IsDebuggerPresent` を確認します（実機キャプチャ上、商用の `410` 内部に SEH ベースのサブステージは存在しません。トラップフラグ `#DB` を用いた SEH デコイは Stage 5 のローダーコード側に別途配置されています）。
* **`520`・`52F`:** `NtQueryInformationProcess` のデバッグ関連情報クラス（`520`）およびカーネルデバッガの状態（`52F`）を照会します。
* **`BE0`:** 旧式の SoftICE / Syser ドライバのデバイス名を確認します。
* **タイミング計測と `#DB` デコイ:** Stage 5 のコード中には、`in eax, dx` によるタイミング読み取りと、`pushfq; or [rsp], 0x100; popfq` によるシングルステップトラップ（SEH ハンドラでデッドコードのデコイ経路をスキップする仕組み）が織り交ぜられています（[ページ保護とローダーコード](page-protection.md)を参照）。
{% endtab %}

{% tab title="仮想マシン検知" %}
* **`540`（VMware バックドア）:** I/O ポート `0x5658` へのプローブ（`in eax, dx`）を実行します。ベアメタル環境や VMware 以外のハイパーバイザでは `#GP` 例外が発生する一方、VMware 上ではマジック値が返ります。
* **`A09`（ハードウェアレジストリのプレフィックス検査）:** `HKLM\Hardware\Description\System\SystemBiosVersion`、`HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation\SystemProductName`、`HKLM\Hardware\Description\System\BIOS\SystemProductName` の値が `Virtual`、`VMware`、`Bochs`、`VBOX`、`VRTUAL`、`Microsoft Hyper-V`、`Parallels` のいずれかで始まるかを検査します（ビルドによっては CPU の仮想化機能ビットも併せて確認します）。
{% endtab %}

{% tab title="システム整合性" %}
* **`C00`・`B00`:** 実際の OS ビルド番号（`0x01A00000 + build`）を設定された Windows 10 以降の最小要件ビルドと比較し（`C00`。PEB の報告ビルド番号を引き下げる単純なバージョン偽装は通用しません）、OS の互換性を確認します（`B00`）。
* **`C01`:** `testsigning` または `disableintegritychecks` が有効な状態でブートされた環境を拒否します。
* **`BD0`:** `C:\Windows\msc.log.log` が存在する場合に起動を中断します。
* **`E55`・`E91`:** `1B40` 系ビルドにおいて、解析ツール系ドライバ（OpenArk や Cheat Engine など）に紐づくシンボリックデバイスリンクの有無をプローブします。
{% endtab %}

{% tab title="プロセス・ホスト検証 (A11 / A15)" %}
* **`A03`:** 親プロセス名を制限します（通常は `explorer.exe` または `cmd.exe` のみ許可）。
* **`A0F`:** ロード済みモジュール（`AppInit_DLLs`、`user32.dll`、`apphelp.dll`、`ShimEng.dll` を含む）を走査し、ホストビルドによってはアプリケーションディレクトリ内の想定外 DLL も拒否します。
* **`A07`・`A01`:** 想定外の外部スレッドを強制終了し（`A07`）、終了できずに残存したスレッドがある場合は起動を中断します（`A01`）。
* **`A11`（DLL ホスト検証）:** 現在のプロセスにマップされているホスト EXE を検査し、`peC` という名前のセクション、または大文字・小文字まで一致する `KeRnEl32.dLl` を参照するインポート記述子のいずれかが存在すれば正当なホストと判定します（Windows ローダーは大文字・小文字を区別せず DLL を解決しますが、この混在表記が CrackProof ホストの目印として機能します）。別の `A11` バリアントでは追加のフラグ引数も検証します。
* **`A15`（DLL シーケンサマーカー）:** 検査処理本体は持たず、保護された DLL のパスで `A09`/`A11` が通過した後に `5D0` の直後で出力されます。ホスト EXE が `A15` を記録することはなく、同じ位置では代わりに `552`/`570` が記録されます。
{% endtab %}

{% tab title="アンチフック" %}
* **`A08`・`A04`:** `System32` からディスク上の正規 `ntdll.dll` と `kernel32.dll` を新たにマップし、無改変の `.text` バイト列を上書きコピーすることでユーザーモードのインラインフックを無効化します。さらに `A04` は、ディスク上のシステム DLL 自体が改変されている場合にも起動を中断します。
{% endtab %}
{% endtabs %}
