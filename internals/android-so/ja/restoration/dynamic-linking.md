---
description: "動的シンボルテーブル・再配置・PLT スロット・コンストラクターの再構築と PT_LOAD への配置。"
icon: link
---

# 動的リンク

中抜きされた `PT_LOAD` のバイト列を主コンテナー（モジュール `0x9D`）から作業用 ELF イメージへ書き戻したあと、静的復元では CrackProof が削除またはモジュール `0x9D`・`0x9E`・`0x96`・`0x98` に分割した動的シンボルテーブルや再配置テーブルなどの動的リンク構造を再構築します。

{% stepper %}
{% step %}
## 隠蔽シンボルの復元とプロテクター末尾インポートの除去

モジュール `0x9E` の先頭には `{u32 blob_size, u32 secondary_record_count}` があり、続く `+0x08` に `{u32 count, u32 symbol_offset, u32 index_offset, u32 string_offset}`、24 バイトの `Elf64_Sym` エントリ `count` 個、書き込み先の `.dynsym` インデックス（`u32`）`count` 個、および NUL 終端シンボル名（末尾に 0〜3 バイトのゼロパディング）が並びます。各パッチの書き込み先は重複のない `0 < target_index < symbol_count` でなければならず、`st_name` が指すシンボル名は `.dynstr` の範囲内に収まる必要があります（ゼロ埋め領域への書き込み、または既存の同一文字列との一致）。

`0x9E` の最大 `target_index` より後ろに残る末尾シンボルが、プロテクターの注入したインポート（`{"dlerror", "__stack_chk_guard", "__stack_chk_fail"}`）のみである場合、補助シンボルを追加する前にそれらの末尾シンボルと参照元の再配置エントリを除去します。
{% endstep %}

{% step %}
## 補助シンボルの追加と再配置インデックスの逆置換

`0x9D` から展開される補助 ELF コンテナーには、`relocation1`（`.rela.dyn` 候補）、`relocation2`（`.rela.plt` 候補）、補助 `.dynsym`（インデックス `0` の NULL エントリと `N - 1` 個の外部シンボル）、および補助 `.dynstr` が格納されています。NULL 以外の補助シンボルを本体の動的シンボルテーブル（`.dynsym`）末尾へ追加し、対応する文字列で `.dynstr` を拡張します。あわせて `.gnu.version` には `VER_NDX_GLOBAL = 1` を割り当て、`.gnu.version_r` は復元された本体イメージのものをそのまま維持します。

モジュール `0x96` が存在する場合（`N > 1`）、`relocation1` と `relocation2` 内の非ゼロ補助シンボルインデックス（`1..N-1`）には、`0x96` から抽出した 32 ビットの `auxiliary_symbol_seed` を用いて再配置テーブルの行 `row` ごとにローテーションが施されています。

```text
s2       = (seed * seed) & 0xFFFFFFFF
left     = ((s2 >> (row & 0x1B)) + 0x1BC5) & 0xFFFFFFFF
right    = (((s2 << (row & 3)) & 0xFFFFFFFF) + 0x2048) & 0xFFFFFFFF
rotation = (left | right) % (N - 1)
```

`N - 1` を法として行ごとのローテーションを元に戻したうえで `old_symbol_count - 1` を加算し、各 `r_info` が統合後の `.dynsym` スロットを指すように補正します。
{% endstep %}

{% step %}
## 除外された 5 つの `libc` PLT スロットの特定

CrackProof は標準 `libc` の文字列・メモリ操作関数のうち最大 5 つ（`strlen`、`strcmp`、`memset`、`strcpy`、`strchr`）を `relocation2` から除外するため、`.got.plt`（先頭 `0x18` バイトのヘッダー以降）に再配置から参照されないスロットが残ります。復元処理では各空きスロットを `.plt + 0x20 + slot * 0x10`（およびコンパイラが生成した `ADRP X16/X17; ADD; BR` ベニア）に対応付け、`.text` 全体の AArch64 呼び出し箇所における引数レジスタと戻り値の使われ方を解析します。一致した関数に対して `SHN_UNDEF` かつ `STT_FUNC` のシンボルを追加し、欠落していた `R_AARCH64_JUMP_SLOT`（`0x402`）レコードを `.rela.plt` に出力します。
{% endstep %}

{% step %}
## `.rela.dyn` の正規化・シンボルハッシュ再構築・コンストラクター復元

`.rela.dyn` のレコード（`R_AARCH64_ABS64 = 0x101` または `R_AARCH64_GLOB_DAT = 0x401`）のうち、対象シンボルが定義済み（`st_shndx != SHN_UNDEF`）のものは、`r_addend = st_value + r_addend` とした `R_AARCH64_RELATIVE`（`0x403`）へ変換します。すべての `R_AARCH64_RELATIVE` エントリを `.rela.dyn` の先頭に集めて `r_offset` の昇順にソートし、その先頭領域のエントリ数で `DT_RELACOUNT` を更新します。

入力 ELF が持つシンボルハッシュセクション（`.gnu.hash`、SysV `.hash`、またはその両方）は、確定した `.dynsym` に基づいて再構築します。モジュール `0x98` が存在する場合は、ステップ数制限付きの AArch64 インタープリターを `entry_offset` から実行し（`X0 = runtime`、`[X0 + 8] = image_base` を渡し、`RET` 時の `W0 == 1` を検証）、隠蔽されていたコンストラクター関数ポインターを回収します。その後、`.init_array` 内の Stage 1 ブートストラップスロットを本来の関数ポインターで置き換え、`RET` のみ（`0xD65F03C0`）のダミーエントリを除去して、`.init_array` / `.fini_array` のセクションサイズおよび `DT_INIT_ARRAYSZ` / `DT_FINI_ARRAYSZ` を更新します。
{% endstep %}

{% step %}
## 再構築したテーブルのインプレース配置または末尾 `PF_R` `PT_LOAD` への追加

再構築した `.dynsym`、`.gnu.version`、ハッシュテーブル、`.dynstr`、`.rela.dyn`、および `.rela.plt` が `.dynsym` 開始位置からの元のファイル領域に収まる場合は、その場（インプレース）に書き戻します。テーブルの拡張によって元の領域を超える場合は、既存の `PT_LOAD` セグメントにおける最大の `p_align` にアラインした読み取り専用（`PF_R`）の `PT_LOAD` セグメントをファイル末尾へ追加し、`DT_SYMTAB`、`DT_STRTAB`、`DT_STRSZ`、`DT_GNU_HASH` / `DT_HASH`、`DT_VERSYM`、`DT_RELA`、`DT_RELASZ`、`DT_JMPREL`、`DT_PLTRELSZ` を更新します。

マップ済みバイトを上書きせずに追加分の `Elf64_Phdr` を挿入するため、プログラムヘッダーテーブル直後に空き領域があればそれを利用し、空きがない場合は `PT_LOAD` 内の冗長な `PT_NOTE` ヘッダー（`PT_NOTE` が 2 つ以上存在する場合）を再利用するか、プログラムヘッダーテーブル自体を追加した `PT_LOAD` の先頭へ移動して `e_phoff` と `PT_PHDR` を更新します。
{% endstep %}
{% endstepper %}
