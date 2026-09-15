---
description: "工作區佈局以及 Windows 與 Android 恢復流水線。"
---

# 設計

Senbei 是完全靜態的解包器。它讀取受保護字節，重放保護算法，驗證結果，並寫出恢復後的映像，全程不啟動、不附加受保護程序。

## crate 佈局

工作區由七個 crate 組成；瀏覽器綁定 `senbei-wasm` 是工作區之外的獨立 crate。`senbei-cli` 是命令行入口，`senbei-io` 負責文件系統編排，`senbei-pe` 與 `senbei-elf` 提供基礎格式解析，`senbei-crypto` 提供共享原語，`senbei-metadata` 恢復元數據，`senbei-engine` 負責保護方案專屬的流水線。

單一平臺的源碼直接放在 `src/` 下。多平臺 crate 把平臺代碼放在 `src/windows/` 與 `src/android/` 下，共享代碼直接放在 `src/` 下。

```text
senbei-cli/src/main.rs
senbei-crypto/src/
senbei-crypto/src/android/
senbei-crypto/src/windows/
senbei-elf/src/
senbei-engine/src/windows/
senbei-engine/src/android/
senbei-io/src/
senbei-io/src/android/
senbei-io/src/windows/
senbei-metadata/src/
senbei-metadata/src/windows/
senbei-metadata/src/android/
senbei-pe/src/
senbei-wasm/src/
```

`senbei-pe` 與 `senbei-elf` 負責經過驗證的格式模型、地址映射與 ELF 動態哈希輔助。它們不依賴解包引擎、文件系統代碼或平臺保護邏輯。

## Windows 引擎

`senbei-engine/src/windows/` 包含 PE 檢測、佈局發現、EXE 與 DLL 恢復、確定性塊並行以及結構完整性檢查。候選佈局先經過試解密與驗證，然後才會被接受為輸出。

外置伴生輸入重建為 `stub[..4096]` 後接匹配的 `._` 載荷。stub 的導出、TLS 與聲明的 CLR 區域在解包後覆蓋回去，因為這些區域不存在於加密的伴生文件中。託管恢復沿 COR20 目錄以及被引用的元數據、資源、vtable 修復表，按各文件的 RVA 映射進行，保留解密出的方法體。

## Android 引擎

`senbei-engine/src/android/extract/` 解密 stage-1 頭部與 stage-2 記錄流，並寫出臨時模塊工作區。`senbei-engine/src/android/restore/` 把解碼後的映像與修復容器應用到被掏空的 ELF 上，並重建動態鏈接器表。兩個階段在寫輸出前都驗證邊界與表放置。

Windows 保護原語在 `senbei-crypto/src/windows/`，Android 保護原語在 `senbei-crypto/src/android/`。Android 帶種子元數據恢復在 `senbei-metadata/src/android/`；結構化的 MethodDef 變換共享在 metadata crate 根部，因為兩個平臺路徑都使用它。

Android ELF 動態表根據輸入節表及其實際文件範圍定位。原始間隙太小時，恢復會在現有加載映像之後新增一個經過驗證的只讀 `PT_LOAD` 並更新動態標記；它絕不覆蓋相鄰節，也不發出不完整映像。

## 掃描與包

文件夾掃描使用平臺目標名來避免打開批量資產：Windows 候選名為 `.exe`、`.dll` 與 `global-metadata.dat`；Android 候選名為 `.so` 與 `global-metadata.dat`。共享遍歷器在 `senbei-io/src/scan.rs`；平臺名稱過濾與 PE 伴生字節適配在 `senbei-io/src/windows/`，Android 包適配在 `senbei-io/src/android/`。Windows 的 `.exe._`、`.dll._` 伴生文件是其同級 stub 的輔助輸入，不計入跳過數。

APK、APKS、XAPK 文件是容器。Senbei 先讀取它們的 ZIP 清單，必要時跟進嵌套 APK 條目，只提取 `.so` 與精確匹配 `global-metadata.dat` 的條目。提取直接流式寫到臨時文件，壓縮副本與解壓副本不會同時駐留內存。

## 驗證

每個啟發式佈局都使用試跑加驗證。未通過結構檢查、校驗和或表邊界的候選會被拒絕，然後嘗試下一個候選。恢復失敗會報告為錯誤，而不是發出靜默損壞的二進制文件。

PE 完整性檢查驗證頭部、節範圍、入口點映射、導入名、重定位需求與託管元數據簽名。Android 恢復驗證 ELF 範圍、解碼後的容器大小、修復表邊界與重建的動態表。

## WebAssembly

瀏覽器綁定通過 I/O 字節 API 依賴 `senbei-engine`。原生文件系統與 Android 包編排不在瀏覽器工作流內。每次瀏覽器解包都在一次性 worker 中運行，因為 WebAssembly 無法像原生代碼那樣從捕獲的 panic 中恢復。
