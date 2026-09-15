---
description: "識別受支持的 IL2CPP 元數據版本，並還原各 image 的方法 RID 置換。"
---

# 方法令牌

已識別的 IL2CPP 元數據魔數是 `0xFAB11BAF`。受支持的佈局為版本 29、31 與 39，三者共享下文介紹的帶種子五輪 RID 置換。MethodDef 令牌高字節為表號 `0x06`，低 24 位是行標識。

這不是 Windows 的 `-GMD` 重映射。Windows 把每個令牌換成僅由表格順序得到的連續值 `0x06000000 | (local_index + 1)`。Android 路徑是對每個 image 方法塊內部 RID 做帶種子的五輪置換。Windows 規則見 [il2cpp 元數據混淆](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/analysis/il2cpp-metadata)。

## image 區間

對每個原生 image，受保護的方法塊是一段連續 RID 區間。各區間不得重疊，必須覆蓋已聲明的方法記錄，並構成期望 image 順序的一個置換。落在區間外的令牌或重複 RID 會被拒絕。

種子取自受保護記錄（模塊 `0x0C`），不是從相鄰方法推斷。一個已觀察的默認值是 `0xa6fae968`。還原之後再次檢查元數據頭、表偏移、字符串區間和方法令牌引用。

在 IL2CPP 庫上，同一清理也在加載時發生：模塊 `0x0C` 用 hook 替換 `mmap`，並在進程映射 `global-metadata.dat` 時還原令牌。同一家族的原生庫不攜帶 `0x0C`。見[運行時模塊](../runtime/modules.md)。

## 五輪逆變換

設 `low`/`high` 是某個 image 的閉區間 RID 界，`count = high - low + 1`（`count ≥ 2`），`key = (seed % (count / 2)) + count / 4`。對加密 RID `rid`：

```
value = rid - low
repeat 5 times:
    mirror = count * 2 - 1
    if value is odd: value = mirror - value
    value >>= 1
    if value >= count: value = mirror - value
    value = value - key          (mod 2^32 wrap)
    if value > count: value = value + count
rid' = value + low
```

新令牌是 `0x06000000 | rid'`。對工具而言清理是冪等的：若各令牌已經是按 image 的規範順序，則檢測出來並保持不動，而不是再做一次逆變換。

表常量因版本而異。版本 29 與 31 的 type 和 image 佈局與 Windows 版本 31 表相同（types `@0xA0` 步長 `0x58`，images `@0xA8` 步長 `0x28`；type `.methodStart +0x24` / `.method_count +0x40`，image `.typeStart +0x08` / `.typeCount +0x0C`），僅方法行不同：

| 版本 | 方法表 | 方法步長 | `.token` 偏移 |
| --- | --- | --- | --- |
| 29 | `@0x30` | `0x20` | `+0x14` |
| 31 | `@0x30` | `0x24` | `+0x18` |

版本 39 用 12 字節 `(offset, size, count)` 節記錄表取代固定頭部，並使用變寬索引（1、2 或 4 字節，按各表的 count 選取）；其方法、類型與 image 步長由這些寬度推導。其他任何版本都必須拒絕，而不是用錯誤的佈局解碼。
