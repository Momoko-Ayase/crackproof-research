---
description: "ユーザー空間での NativeBridge・ptrace・メモリ読み取り監視・APK 署名検証。"
icon: user-shield
---

# 環境検査と整合性チェック

Windows 版とは異なり、Android 版の CrackProof はカーネルドライバーを持たず、すべてユーザー空間で動作します。各種プローブは多段ストリームの展開と並行して、Stage 1、Stage 2、および[ランタイムモジュール一覧](modules.md)に記載されたワーカーモジュール群にわたって実行されます。

## プロセス環境と ABI 変換レイヤーの検査

* **自己マッピングと環境変数:** Stage 1 は `/proc/self/maps` を解析して実体の ELF ファイルを特定し、Stage 2 はマップ情報のコンテキストを保持しつつ `/proc/self/environ` を検査します。
* **x86 上の ARM バイナリ変換（NativeBridge）:** `/system/lib/libhoudini.so` や `/system/lib64/arm64/nb/` の有無を調べ、ネイティブ AArch64 実行ではなく x86 上の ARM 変換レイヤーで動作していないかを判定します。
* **ファイルシステムと `libc` の検証:** モジュール `0x8F` は `/proc/self/cmdline`、`uid` / `gid` / `tid`、およびファイルの所有者・パーミッションを検査します。モジュール `0x60` はシステムライブラリディレクトリやランタイムパスを走査し、モジュール `0x20` は対象 ELF ヘッダー、`/proc/self/maps`、および現在ロードされている `libc` マッピングを検証します。

## ヘルパープロセスと `PTRACE_SEIZE`

解析対象の IL2CPP ビルドでは、ART や VM ライブラリの初期化後、保護された `.so` が `dlopen` される前に補助プロセスを `fork` します。子プロセスは親プロセスへ `PTRACE_SEIZE | PTRACE_O_EXITKILL` でアタッチし、カーネルの `ptrace` アタッチ枠を占有するとともに、いずれかのプロセスが終了した際にアプリ全体を連動して終了させます。保護された `.so` がロードされる前に `fork` が行われるため、`/proc/<child>/maps` に対象ライブラリは現れません。

## `/proc/<pid>/mem` 監視とページ保護属性

確認されたビルドでは、`/proc/<pid>/mem` を開いて読み取ると数秒以内にプロセスが強制終了します。一方、`/proc/<pid>/maps`、`cmdline`、`status` の読み取りや、`process_vm_readv` を経由したメモリ読み取りでは終了は発生しませんでした。モジュール `0x9B` によるセグメント復元が完了したあと、実行可能ページは読み取り可能な状態（`PROT_READ | PROT_EXEC`）のまま維持され、Android 版では `PAGE_NOACCESS` とページフォルトを用いたオンデマンドページ暗号は導入されていません。

## APK 署名とネットワーク時刻の検証

モジュール `0x40` は `base.apk` および Split APK の署名を、APK Signature Scheme v3.1、v3、v2、JAR 署名（v1）の順に検証します。モジュール `0x02` は UDP ポート 123 で NTP サーバーへ問い合わせを行い、返されたタイムスタンプを設定された許容範囲と比較します。モジュール `0x69` は短命なプローブ用子プロセスを生成し、その終了ステータスを確認します。

## リンカーのモジュールリストからの秘匿

Stage 2 のインタープリターと各ワーカーモジュールは匿名 `mmap` 領域（セットアップ中は多くの場合 `RWX`）に配置され、コールバック完了後に自身のメモリをゼロ埋めまたは上書き消去できます。Windows 版における[手動マップされたヘルパー DLL](https://app.gitbook.com/s/XSPACE_WINDOWS_JA/runtime/mapped-modules) と同様、これらのモジュールは Bionic の `dl_iterate_phdr` や `soinfo` リストには一切現れません。
