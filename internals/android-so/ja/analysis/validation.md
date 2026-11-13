---
description: "保護された Android ELF64 共有ライブラリと IL2CPP メタデータの段階的な検証項目。"
icon: list-check
---

# 検証チェックリスト

解析対象のすべての Android 共有ライブラリ（`.so`）と `global-metadata.dat` は、以下の構造チェックを順番に通過する必要があります。必須の不変条件に 1 つでも違反した場合は、不完全な出力ファイルを生成せず直ちに復元処理を中断します（フェイルクローズ）。

{% stepper %}
{% step %}
## ELF の認識と `SHT_LOUSER` の境界検証

* リトルエンディアンの `ELF64`、`EM_AARCH64`（`183`）、`e_phentsize == 0x38`、`e_shentsize == 0x40`、および有効な UTF-8 の `.shstrtab` を備えていることを確認します。
* `.dynsym`、`.dynstr`、`.gnu.version`、`.gnu.version_r`、および少なくとも 1 つのシンボルハッシュセクション（`.gnu.hash` または `.hash`）が存在することを必須とします。さらに復元時は `.dynamic`、`.rela.dyn`、`.rela.plt` がそれぞれ 1 つ存在することを要求します。
* セクションヘッダーテーブルの末尾エントリとして `SHT_LOUSER`（`0x80000000`）の専用セクションがただ 1 つ存在し、ファイル上の `PT_LOAD` 終端を 16 バイト境界に切り上げた位置から始まっていること（隙間がある場合はゼロパディングされていること）を確認します。
{% endstep %}

{% step %}
## Stage 1 と Stage 2 ストリームの抽出

* `section_offset + outer_size` にある 32 バイトの Stage 1 ワードヘッダーを復号し、`reserved == 0`、`size_copy == payload_size`、`payload_size > 0 && payload_size % 4 == 0`、`payload_offset >= 0x20`、`payload_offset + payload_size <= section_size - outer_size`、`entry_offset < payload_size`、および `protect_size <= payload_size` をすべて満たすことを確認します。
* Stage 2 の `0x5C` レコード記述子テーブルを最小の非ゼロペイロードオフセット手前までパースし（個数は `dw0`、上限 256）、すべてのスライスについて `id_copy == command_id` と親ストリーム内の境界を確認します。
* すべての Huffman / LZ ブロックにおいて、圧縮ビット列が過不足なく消費されていること（`div_ceil(consumed_bits, 8) == src_len`）、出力サイズが厳密に一致すること（`output_pos == out_len`）、および未処理状態が残っていないこと（`pending == 0`）を確認します。
* 基本モジュール `0x9B`、`0x9D`、`0x9E` が揃っていることを確認します（`0x96`、`0x98`、`0x0C` は存在する場合に使用）。SHA-256 ダイジェストが同一のモジュールは重複排除し、同一モジュール ID でダイジェストが異なる競合はエラーとして棄却します。
{% endstep %}

{% step %}
## 動的リンクテーブルの再構築と ELF 出力

* `0x9E` の隠蔽シンボルインデックス（`0 < target_index < symbol_count` かつ一意）と `.dynstr` の境界を検証します。プロテクター末尾シンボル（`dlerror`、`__stack_chk_guard`、`__stack_chk_fail`）の除去、`0x96` 存在時の補助シンボルインデックス逆置換、除外された `libc` PLT スロットの特定、定義済みシンボル再配置のソート済み `R_AARCH64_RELATIVE` 先頭領域への正規化（`DT_RELACOUNT` 更新）、および `0x98` 存在時のコンストラクター復元を実行します。
* 再構築したテーブルを `.dynsym` 以降の既存領域または末尾に追加した `PF_R` の `PT_LOAD` へ配置し、`SHT_LOUSER` の削除、`e_entry` の `0` クリア、ロード可能セグメント直後への非 `SHF_ALLOC` セクション再配置を行ったうえで、アトミックに書き出してディスクから再パースします。
* 書き込み後の必須チェック（パース妥当性、`PT_LOAD` のファイル境界、`.shstrtab`、`SHT_LOUSER` 不在、`e_entry == 0`、`.dynsym` / `.rela.dyn` / `.rela.plt` の厳密なエントリ数一致）を適用し、テーブル間のリンカー整合性診断を記録します。
{% endstep %}

{% step %}
## IL2CPP メタデータの検証

* マジック値 `0xFAB11BAF` を確認し、バージョン `24`（同一アプリのモジュール `0x0C` と対応付けた `v24.1`）、`29`、`31`（シード付き 5 ラウンド逆置換およびテーブル順の `-GMD` フォールバック）、または `39`（12 バイト記述子のコンパクトディレクトリ）の検証済みテーブルレイアウトであることを要求します。
* すでに正規状態のメタデータは無変更のまま維持し（べき等性）、復元後にすべてのメソッドがいずれか 1 つのイメージ（`Il2CppImage`）に属してテーブル上で連続していることと、正規の `0x06000000 | rid` または `0..active_count` の範囲に収まっていることを検証します。
{% endstep %}
{% endstepper %}
