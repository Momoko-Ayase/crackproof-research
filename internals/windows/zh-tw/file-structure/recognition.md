---
description: "基於內容的 KONN 偵測、PE32/PE32+ 原生與受控分類，以及容器版型維度。"
icon: fingerprint
---

# 格式辨識與組建家族

## 基於內容的辨識與模組分類

同時符合下列兩項條件時，檔案即具備外層容器特徵：

1. 檔案長度至少為 `4128` 位元組（`0x1020`），且 `e_lfanew`（`u32@0x3C`）指向合法的 `PE\0\0` 簽章。
2. 對位移 `4096` 執行 `header_kdf` 後，得出 `info[1] == 0x4E4E4F4B`（`KONN`）。

通過上述檢查代表該檔案為候選容器；完整驗證仍須確認 `info` 範圍未越界、階段描述子合法，並通過階段校驗和或試解壓縮檢查。

完成容器辨識後，可依標準 PE 標頭欄位將目標分為四種模組類型：

* `IMAGE_FILE_HEADER.Characteristics & 0x2000`（`IMAGE_FILE_DLL`）區分 DLL 與 EXE。
* 資料目錄 `14`（`IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR`，在 PE32 位於可選標頭 `+96`，在 PE32+ 位於 `+112`）區分受控組件（.NET）與原生二進位檔。

| `IMAGE_FILE_DLL` | CLR RVA（`DD[14]`） | 模組類型 |
| --- | --- | --- |
| `0` | `0` | `native-exe` |
| `0` | 非零 | `managed-exe` |
| 非零 | `0` | `native-dll` |
| 非零 | 非零 | `managed-dll` |

受控 EXE 與原生 EXE 共用相同的 EXE 式容器結構。

```python
MAGIC_KONN = 0x4E4E4F4B  # the shell stamp

def detect(file_data):
    """Return ("native-exe" | "managed-exe" | "native-dll" | "managed-dll",
    magic) for a protected file, or None when the file is not protected by
    this scheme."""
    if len(file_data) < 4128:
        return None
    pe_off = get_u32(file_data, 0x3C)
    if file_data[pe_off:pe_off + 4] != b"PE\0\0":
        return None
    info = header_kdf(file_data)
    if info[1] != MAGIC_KONN:
        return None

    characteristics = get_u16(file_data, pe_off + 4 + 18)   # IMAGE_FILE_HEADER
    is_dll = bool(characteristics & 0x2000)                 # IMAGE_FILE_DLL

    # COM descriptor (CLR) data directory: managed vs native, EXE and DLL alike.
    # Data directories start at optional-header +96 on PE32, +112 on PE32+.
    opt_magic = get_u16(file_data, pe_off + 24)             # 0x10B / 0x20B
    dd_base = 112 if opt_magic == 0x20B else 96
    clr_rva = get_u32(file_data, pe_off + 24 + dd_base + 14 * 8)
    managed = bool(clr_rva)

    if is_dll:
        return ("managed-dll" if managed else "native-dll", info[1])
    return ("managed-exe" if managed else "native-exe", info[1])
```

{% hint style="info" %}
讀取資料目錄前務必先檢查可選標頭魔術數字（`0x10B` 或 `0x20B`）：`DD[14]` 在 PE32 位於 `pe + 0xE8`，在 PE32+ 則位於 `pe + 0xF8`。若讀錯位移，可能將 32 位元原生二進位檔誤判為受控組件。
{% endhint %}

## 實測版型維度

受保護的 Windows 檔案可依四項結構特徵分類（實務上僅出現特定組合：專用 DLL 容器僅限 64 位元帶標記版型，外部伴生檔案則固定採用 PE32+ EXE 式外殼）：

* **位元寬度：** PE32+（`0x20B`，64 位元）與 PE32（`0x10B`，32 位元）共用 `header_kdf` 與核心加密演算法，但採用不同的設定表、階段數與匯入表／標頭重建規則（其中 PE32 另分為標準型與精簡型外殼變體）。
* **模組類型：** `native-exe`、`managed-exe`、`native-dll` 與 `managed-dll`。即使受控組建在磁碟上保留明文的 `COR20` 標頭與 `BSJB` 中繼資料根節點，其 IL 方法本體仍存放在加密與壓縮的區段負載中。
* **64 位元設定探索方式：**
  * **帶標記版型（早期典型）：** Stage 5 內含字面標記 `70 6D 00 00 63 6D 00 00`（`"pm\0\0cm\0\0"`）與 `00 00 00 40 01 00 00 00`（`0x40000000, 1`），各描述子表指標皆位於固定相對位移。
  * **無標記版型（近期組建）：** 省略上述兩組標記，改以 LFSR 掃描、`trial_byte_rotate2` 範圍檢查、`fileCS` 距離評分與試解壓縮來定位 Stage 5 各欄位與位元組碼存根。
* **DLL 容器形式：**
  * **專用 DLL 版型：** 僅用於 64 位元 DLL（`0x20B`）的容器，其設定表固定自 `info[6] + 5592`（`0x15D8`）開始。
  * **EXE 式外殼：** 以 EXE 使用的分階段外殼封裝 32 位元或 64 位元 DLL，並支援拆分為[外部伴生檔案（`._`）](companion-layout.md)。
