---
description: "ページ暗号化ホスト EXE、ネイティブプラグイン DLL、マネージド DLL の匿名化実行時ログ。"
icon: file-lines
---

# サンプルデバッグログ

起動前に `%temp%` 配下へ各バイナリ固有の12桁16進数フォルダーを作成して採取した、実際の CrackProof 実行時ログです（[デバッグログ出力](https://app.gitbook.com/s/DDUo0VKfH9uzyTcguGIx/runtime/startup-status#debug-logging)を参照）。ファイルパスと製品名は汎用的なプレースホルダーに置き換えていますが、オプションフラグ、ステータスコード、アドレス、hook 対象 API の一覧は実出力そのままです。

## ログの構造

* **1行目:** 保護された EXE または DLL のフルパス。
* **2行目:** ビルド時にモジュールへ埋め込まれたパッカーのオプショントークン（`-CF`、`-CP`、`-PP` など）。
* **3〜4行目:** 開始タイムスタンプと16進表記のモジュールロードベースアドレス。
* **本文行:** 12ビットの[ステータスコード](https://app.gitbook.com/s/DDUo0VKfH9uzyTcguGIx/runtime/startup-status#the-boot-sequence-and-status-codes)。インデントされた `000`..`00D` の詳細行には、ステージパラメーター、ドライバー名、hook された関数のアドレスが記録されます。
* **末尾行:** 終了タイムスタンプと `AAA-BBB-CCC` 形式の結果コード（正常起動時は `000-000-000`）。

## 採取ログ一覧

{% tabs %}
{% tab title="ホスト EXE（ページ暗号化あり）" %}
このトレースから確認できる主な挙動は次のとおりです。

* **`C00`（`01A065F4 01A037AB`）:** 各 DWORD は `0x01A00000 + build` 形式であり、ホストの Windows ビルド `26100`（`0x65F4`）と許容最小ビルド `14251`（`0x37AB`）を記録しています。
* **`C03` と `C04`:** 第2世代ドライバー `Htsysm7679` を初期化し（[Htsysm カーネルコンポーネント](https://app.gitbook.com/s/DDUo0VKfH9uzyTcguGIx/runtime/kernel-components)を参照）、非互換なシステムコールの前後で Protected Process 状態を切り替えるために `kernel32` / `kernelbase` / `ntdll` の 15 個の API を hook しています。
* **`610 -> 640 -> 655 -> 6E1 -> 800..840 -> 660 -> 280`:** 実行可能セクションを一括復号し（`640`）、再配置を適用したあと（`655`）、`KiUserExceptionDispatcher` を hook して各ページを `PAGE_NOACCESS` に変更し（`840`）、ページ保護設定後の引き渡し処理 `660` を経て OEP へジャンプしています（`280`）。

```text
E:\Package\app.exe
 -CF -CP -C2 -E2 -CC -T12 -RC3 -GWH -DA -DD -PP -I -EL5 -CK2 -CD1 -CD2 -CD3 -CD4 -EUT64 -DE -NCP2 -NC -NE -NCC2 -NRC -NDA3 -NEL -NEL2 -NEL3 -NEL4 -NELA -NEVS -NERR -NWEB -NEUT32 -NDEP1 -NDC -NPD
2026/05/15 04:55:07.178
 00007FF7`B2850000
200
 000 00001000 00000000 
410
510
520
540
560
A03
561
C00
 001 01A065F4 01A037AB
C01
C02
C03
 001 Htsysm7679
 005 E0ED7281 FFFFF806 386C0000 A6D4B2B6
C04
 004 05F8 00220000
 003 03 00007FF9`2F7BAA40 kernel32.dll!CreateProcessInternalA
 003 03 00007FF9`2DB4DCD0 kernelbase.dll!CreateProcessInternalA
 003 03 00007FF9`2F7BAAC0 kernel32.dll!CreateProcessInternalW
 003 03 00007FF9`2DB4E320 kernelbase.dll!CreateProcessInternalW
 003 03 00007FF9`2F7A2E20 kernel32.dll!CreateRemoteThread
 003 03 00007FF9`2DB6E050 kernelbase.dll!CreateRemoteThreadEx
 003 03 00007FF9`304BF7C0 ntdll.dll!LdrLoadDll
 003 03 00007FF9`305E2430 ntdll.dll!NtCreateSection
 003 03 00007FF9`305E2CA0 ntdll.dll!NtAlpcSendWaitReceivePort
 003 03 00007FF9`2F7A49A0 kernel32.dll!CreateActCtxW
 003 03 00007FF9`2DBA1160 kernelbase.dll!CreateActCtxW
 003 03 00007FF9`305E2270 ntdll.dll!NtDuplicateObject
 003 03 00007FF9`305E2F60 ntdll.dll!NtConnectPort
 003 03 00007FF9`305E1FB0 ntdll.dll!NtOpenProcess
 003 03 00007FF9`305E4200 ntdll.dll!NtOpenThread
A09
A0F
A08
A07
 002 01 00
5D0
552
570
 001 00007FF9`2F79F7D0 00007FF7`B2933A50 00007FF7`B2933560 00007FF7`B2933740
 00C 001F
 00D 0000 0000 0000 0000 0000 0000
590
5B0
598
5A0
A06
 003 23 00007FF9`2F9C3420 user32.dll!!SetFocus
 003 03 00007FF9`2DA71C20 win32u.dll!NtUserSetFocus
 003 03 00007FF9`26F25580 uxtheme.dll!!ThemeInitApiHook
 003 03 00007FF9`2F97D310 user32.dll!CreateWindowExA
 003 03 00007FF9`2F97D920 user32.dll!CreateWindowExW
5C0
5E1
610
640
655
6E1
800
 001 00007FF7`B294DC00
810
820
840
 002 00007FF7`B28F3010 00007FF7`B294B950 00007FF7`B294B820
 001 04F0
660
280
2026/05/15 04:55:07.278
000-000-000
```
{% endtab %}

{% tab title="ネイティブプラグイン DLL（一括復号）" %}
このトレースから確認できる主な挙動は次のとおりです。

* **`A11` -> `5D0` -> `A15`:** `A11` でホスト EXE が CrackProof のホストマーカーを持つことを検証し、`5D0` の後にホスト検証通過を示す純粋な DLL シーケンサーマーカーとして `A15` が出力されています。
* **`640` / `840` なし（`-NCP`）:** セクションは `610` で1度だけ復号され、`655` で再配置された後、すべてのコードページをメモリ上に常駐させたまま `800 -> 830 -> 280` と遷移しています。

```text
E:\Package\app_Data\Plugins\native_plugin.dll
 -CF -C2 -E2 -CC -T12 -RC3 -GWH -DA -DD -PP -I -EL5 -CK2 -CD1 -CD2 -CD3 -CD4 -DE -NCP -NCP2 -NC -NE -NCC2 -NRC -NDA3 -NEL -NEL2 -NEL3 -NEL4 -NELA -NEVS -NERR -NWEB -NEUT32 -NEUT64 -NDEP1 -NDC -NPD
2026/05/15 04:55:14.518
 00007FF8`31480000
200
 000 00001000 00000000 
510
540
560
A09
A11
5D0
A15
590
5B0
5A0
5C0
5E1
610
655
6E1
800
 001 00007FF8`317C4000
830
280
2026/05/15 04:55:14.619
000-000-000
```
{% endtab %}

{% tab title="マネージド DLL" %}
このトレースから確認できる主な挙動は次のとおりです。

* CLR DLL 向けの最小シーケンスを実行しています。`510` のローダー CRC、`A09` の VM レジストリ検査、`A11` のホスト EXE 検査、復号前処理 `5D0..5A0`、`610` でのセクション／メソッド本体復号を経て、ドライバー初期化や再配置、ページ暗号化（`PAGE_NOACCESS` 設定）を行わずにそのまま `280` で制御を引き渡しています。

```text
E:\Package\app_Data\Managed\Assembly-CSharp.dll
 -CF -CP -C2 -E2 -CC -T12 -RC3 -GWH -DA -DD -PP -I -EL5 -CK2 -CD1 -CD2 -CD3 -CD4 -EUT64 -DE -NCP2 -NC -NE -NCC2 -NRC -NDA3 -NEL -NEL2 -NEL3 -NEL4 -NELA -NEVS -NERR -NWEB -NEUT32 -NDEP1 -NDC -NPD
2026/05/15 04:55:09.342
 00000174`0D290000
200
 000 00001000 00000000 
510
560
A09
A11
5D0
590
5B0
5A0
610
280
2026/05/15 04:55:09.368
000-000-000
```
{% endtab %}
{% endtabs %}
