---
description: "命令行用法：文件、包與文件夾目標，標誌與退出碼。"
---

# 用法

```text
senbei <file|folder> [--out DIR] [-v|--verbose] [-q|--quiet]... [--scan-all] [--no-log] [--no-pause] [-V|--version] [-h|--help]
```

## 單個文件

Senbei 把輸出寫到 `<parent>/unpack/` 下，並在擴展名前插入 `.unpack`。`--out DIR` 同時改變輸出目錄與日誌目錄。

```cmd
senbei app.exe
senbei app.exe --out C:\out
```

對於 `global-metadata.dat`，只有方法令牌發生變化時 Senbei 才寫出 `global-metadata.unpack.dat`。不支持的元數據版本保持原樣，並報告為跳過。

## Android 目標

Senbei 從加密載荷節恢復受保護的 `.so` 文件，寫出為 `libil2cpp.unpack.so` 或對應的輸入名。APK、APKS、XAPK 文件按容器處理：Senbei 先讀取清單，必要時跟進嵌套 APK，只提取 `.so` 與精確匹配 `global-metadata.dat` 的條目。

如果恢復後的庫包含內嵌元數據，Senbei 會把解包後的數據塊作為 `global-metadata.unpack.dat` 寫到它旁邊。內容相同的鬆散文件與包內條目只恢復一次，優先取鬆散文件。

## 文件夾模式

文件夾模式遞歸遍歷，跳過名為 `unpack` 的目錄，並把識別到的輸出按相對路徑寫到 `<root>/unpack/` 或 `--out DIR` 下。Windows 候選名為 `.exe`、`.dll` 與 `global-metadata.dat`；Android 候選名為 `.so` 與 `global-metadata.dat`。匹配的 `.exe._`、`.dll._` 載荷由其 stub 消費，不計入跳過數。

託管 DLL 伴生文件在原始 DLL 中保留 CLR 元數據及相關運行時表。DLL 與其匹配的 `._` 文件必須同時可用；Senbei 從 DLL 恢復聲明的 CLR 區域，同時保留從伴生文件解密的方法體。被引用區域缺失或不可讀時報告為錯誤。

彙總行形如 `12 unpacked · 3 skipped · 0 errors · 1 suspect · 2 metadata`；打開過包時追加包計數。每個文件相互隔離，單個目標失敗不會中斷文件夾運行。

## 完整性檢查

PE 輸出會檢查有效頭部、節範圍、入口點映射、可讀導入名、重定位需求與託管元數據簽名。Android 輸出在 ELF 恢復過程中驗證，包括解碼後的容器大小、修復表邊界與重建的動態表。

乾淨的報告不是正確性證明，但未通過的報告可以可靠地說明輸出已損壞。可疑 PE 文件仍會寫出並單獨計數。

## 標誌

| 標誌 | 行為 |
| --- | --- |
| `--out DIR` | 把輸出與日誌寫到 `DIR` 下。 |
| `-v`, `--verbose` | 打印各階段進度。 |
| `-q`, `--quiet` | 隱藏進度與逐文件行；重複使用可抑制全部標準輸出。 |
| `--no-log` | 不寫運行日誌。 |
| `--scan-all` | 探測每個選定的目標名候選，包括低於大小下限的文件。 |
| `--no-pause` | 關閉便於資源管理器雙擊運行的 Windows 退出提示。 |
| `-V`, `--version` | 打印版本並退出。 |
| `-h`, `--help` | 顯示用法。 |

## 退出碼

| 代碼 | 含義 |
| --- | --- |
| `0` | 請求的恢復已完成，沒有錯誤。 |
| `1` | 目標失敗、掃描探測不可讀，或單文件恢復出錯。 |
| `2` | 命令行無法解析。 |
