---
description: "識別受保護 PE 文件的結構檢查，以及不同構建家族的佈局。"
---

# 識別與構建家族

## 識別與分類

受保護文件基於內容識別，與文件名或擴展名無關。初步篩選條件是：

1. 至少 4128 字節長，且 `e_lfanew`（`u32@0x3C`）處有有效 `PE\0\0` 簽名。
2. 對偏移 4096 應用 KDF 得到 `info[1] == KONN`。

這兩項只能確定候選文件。接受具體佈局前，還必須確認每個 `info` 範圍都位於文件內，階段記錄與節記錄邊界有效，並且至少有一項後續校驗和或解碼成功。不能只憑 `KONN` 信任所有派生偏移。

分類使用常規 PE 字段。兩個字段對每個候選都適用；EXE/DLL 與原生/託管相互獨立：

- `IMAGE_FILE_HEADER.Characteristics & 0x2000`（`IMAGE_FILE_DLL`）區分 DLL 與 EXE。
- COM 描述符（CLR）數據目錄——第 14 項，位於可選頭 PE32 `+96` 或 PE32+ `+112` 處——區分託管（.NET）與原生。

四種組合是：

| `IMAGE_FILE_DLL` | CLR RVA | 種類 |
| --- | --- | --- |
| 未置位 | 0 | 原生 EXE |
| 未置位 | 非零 | 託管 EXE |
| 置位 | 0 | 原生 DLL |
| 置位 | 非零 | 託管 DLL |

託管 EXE 使用與原生 EXE 相同的 EXE 風格容器。分類只需要 CLR 目錄這一處 PE 頭差異，它不是第五種佈局家族。

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
用錯數據目錄基址（96 與 112）會讀錯 dword，把 32 位原生映像誤判為託管。必須先讀可選頭 magic。對 EXE 跳過 CLR 檢查會把託管 EXE 併入原生 EXE。
{% endhint %}

## 構建家族

實際樣本中觀察到的受保護文件沿四條軸變化，各軸相互獨立，所有組合都需要處理。

**位寬。** PE32+（可選頭 magic `0x20B`，64 位）與 PE32（`0x10B`，32 位）容器共享頭部/payload 層，但使用完全不同的配置佈局、階段結構與最終 PE 修補。

**對象種類。** 原生 EXE、託管 EXE、原生 DLL 與託管 DLL（見上文分類）。某些託管佈局會在受保護文件中原樣保留 COR20 頭與 BSJB 元數據流。這不表示託管方法體是明文；方法體仍屬於需要按正常流程恢復的節。

**配置佈局。** 64 位加載器配置有兩代：

- **標記佈局**（較舊構建）在加載器最終階段內嵌字節標記 `70 6D 00 00 63 6D 00 00`（`"pm\0\0cm\0\0"`——加載器的雙字母子模塊代碼）與 `00 00 00 40 01 00 00 00`（一個 `0x40000000, 1` dword 對）。每張重要的表都位於這些標記的固定偏移處。
- **無標記佈局**（較新構建，包括以 EXE 風格外殼包裹的 DLL）省略兩個標記。表的位置要根據記錄形態、嵌入式變換程序、指針範圍，以及對壓縮記錄的試解碼共同確定。

**DLL 打包方式。** DLL 有兩種保護形態：

- **專用 DLL 佈局**（較舊）：DLL 專屬容器，其配置塊位於固定偏移（`keys[6] + 5592`），無需掃描錨點。
- **EXE 風格外殼**（較新）：DLL 被套上與 EXE 相同的外殼佈局。下面的外置伴生體拆分即屬於這一家族。
