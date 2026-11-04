---
description: "命令行用法：文件、包與文件夾目標，標誌與退出碼。"
---

# 用法

```text
senbei <file|folder> [--out DIR] [-v|--verbose] [-q|--quiet]... [--scan-all] [--strict-integrity] [--max-entry-mib N] [--max-total-mib N] [--max-entries N] [--max-depth N] [--no-log] [--no-pause] [-V|--version] [-h|--help]
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

`Companion missing?` 表示 Senbei 識別到明確聲明 `._` 後綴的 PE32+ 加載器入口記錄，但未提供伴生文件。把 `<input>._` 放在輸入文件旁邊，保留完整文件名（例如 `module.dll._`），或在瀏覽器中同時添加兩個文件。此檢查會驗證 PE 結構、保護簽名與入口記錄，但不能證明 stub 的每個部分均完好。僅文件較小、節被清空或解包失敗不會觸發此提示。入口記錄損壞或無法識別時，保留原始解包錯誤。

若已提供的伴生文件不足以容納 32 字節配對頭部，或頭部與已識別加載器中的內容不同，Senbei 會報告 `Companion doesn't match`。請使用同一構建中的兩個文件；任一文件都有可能損壞。伴生文件無法讀取時報告文件讀取錯誤。頭部匹配但後續解密失敗時，保留原始解包錯誤。

彙總行形如 `12 unpacked · 3 skipped · 0 errors · 1 suspect · 2 metadata`；打開過包時追加包計數。每個文件相互隔離，單個目標失敗不會中斷文件夾運行。

## 完整性檢查

PE 輸出會檢查有效頭部、節範圍、入口點映射、可讀導入名、重定位需求與託管元數據簽名。Android 輸出在 ELF 恢復過程中驗證，包括解碼後的容器大小、修復表邊界與重建的動態表。

乾淨的報告不是正確性證明，但未通過的報告可以可靠地說明輸出已損壞。可疑 PE 文件仍會寫出並單獨計數。`--strict-integrity` 不改變這一寫出行為，只改變進程退出碼。

## 標誌

| 標誌 | 行為 |
| --- | --- |
| `--out DIR` | 把輸出與日誌寫到 `DIR` 下。 |
| `-v`, `--verbose` | 打印各階段進度。 |
| `-q`, `--quiet` | 隱藏進度與逐文件行；重複使用可抑制全部標準輸出。 |
| `--no-log` | 不寫運行日誌。 |
| `--scan-all` | 探測每個選定的目標名候選，包括低於大小下限的文件。 |
| `--strict-integrity` | 尚未進入已發佈構建。任一輸出未通過靜態完整性檢查（可疑）或任一文件出錯時，以非零狀態退出。默認關閉：可疑輸出仍會寫出，並且除非有文件出錯，進程以 `0` 退出。重複 `-q` 的行為不變。 |
| `--max-entry-mib N` | 尚未進入已發佈構建。僅用於 Android。正數 MiB 上限，約束解壓過程中的單個 ZIP 條目、單個解碼緩衝區、單次工件讀取與單個輸出文件。默認 `2048`（1 MiB = 1,048,576 字節）。 |
| `--max-total-mib N` | 尚未進入已發佈構建。僅用於 Android。正數 MiB 上限，約束文件夾內累計的歸檔字節，以及單個引擎任務中另行記賬的提取與恢復工作。默認 `8192`。這不是進程內存峰值上限。 |
| `--max-entries N` | 尚未進入已發佈構建。僅用於 Android。正數上限，約束歸檔條目與 stage-2 記錄，並跨嵌套歸檔計數。默認 `100000`。 |
| `--max-depth N` | 尚未進入已發佈構建。僅用於 Android。嵌套 APK 與 stage-2 流的嵌套深度上限。根的深度為 `0`，允許傳入 `0`。默認 `32`。 |
| `--no-pause` | 關閉便於資源管理器雙擊運行的 Windows 退出提示。 |
| `-V`, `--version` | 打印版本並退出。 |
| `-h`, `--help` | 顯示用法。 |

## 退出碼

| 代碼 | 含義 |
| --- | --- |
| `0` | 請求的恢復已完成，沒有錯誤。未設置 `--strict-integrity` 時，可疑輸出仍以 `0` 退出。 |
| `1` | 目標失敗、掃描探測不可讀，或單文件恢復出錯。加上尚未發佈的 `--strict-integrity` 後，任一可疑輸出也以 `1` 退出。輸出仍會寫出。超出 Android 資源上限時也以 `1` 退出；Senbei 不會靜默截斷這部分工作。 |
| `2` | 命令行無法解析。資源上限不是無符號十進制整數時屬於命令行錯誤；除 `--max-depth` 外，傳入 `0` 同樣是命令行錯誤。 |
