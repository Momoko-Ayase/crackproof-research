---
description: "HtdpsCmnGetFileInfo が手動マップする埋め込み補助 DLL 群と各モジュールの役割"
icon: layer-group
---

# 手動マップされる補助モジュール

CrackProof は主要なランタイムサブシステムを保護対象バイナリ自身のセクションには置かず、補助 DLL 群をローダーペイロードの内部に埋め込み、2 文字のモジュールコードをキーとする内部ローダー（`HtdpsCmnGetFileInfo`）経由でメモリへ展開します。

## サブモジュール一覧

`HtdpsCmnGetFileInfo` は要求された補助 DLL をプライベートの実行可能メモリ領域に手動マップし（そのため `InLoadOrderModuleList` や `CreateToolhelp32Snapshot` が走査する `PEB` のモジュールリストには現れません）、PE ヘッダからエントリポイントを解決したあと、設定に応じて先頭の `MZ` および `PE\0\0` シグネチャをゼロ消去します。

| 2 文字コード | モジュール名 | ステータス範囲 | 実行時の役割 |
| --- | --- | --- | --- |
| `it` | `HtpecIt.dll` | `Axx` | ユーザーモードの耐改ざん・注入検知・VM レジストリ検査・ホストプロセス検証 |
| `dt` | `HtdpStub2.dll` | `8xx` / アクセス違反発生時 | オンデマンドページ復号ハンドラ（`KiUserExceptionDispatcher` の分岐先）とページ記述子テーブル |
| `cm` | （ユーザーモード補助 DLL） | `Bxx` | 第 1 世代 `Htsysm` ドライバのセットアップ |
| `dm` | （ユーザーモード補助 DLL） | `Cxx` | 第 2・第 3 世代 `Htsysm` ドライバのセットアップおよび IOCTL ハンドシェイク |
| `sk` | `HtsyskNT.dll` | `B21` | 第 1 世代カーネル DLL：カーネル空間の手動マッパーおよびメモリ／I/O プリミティブ |
| `pm` | `HtpecmNT.dll` | `BB0` | 第 1 世代カーネル DLL：プロセス監視および強制終了 |

ページ復号ルーチンとリージョン／ページ記述子配列はいずれも `dt`（`HtdpStub2.dll`）側に保持されているため（[ページ保護とローダーコード](page-protection.md)を参照）、メインの `.exe` や `.dll` モジュールだけをダンプしてもオンデマンド復号ハンドラは含まれません。`dt` を回収するには、プライベート実行可能属性を持つ VAD 領域を探すか、`ntdll!KiUserExceptionDispatcher` 先頭のインラインジャンプを追跡します。カーネル側の対応コンポーネントについては [Htsysm カーネルコンポーネント](kernel-components.md)で解説します。
