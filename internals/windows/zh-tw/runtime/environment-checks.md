---
description: "控制權到達原程序前執行的用戶態與內核輔助檢查。"
---

# 環境與反分析檢查

## 環境與反分析檢查

檢查在解密之前（部分與解密交錯）運行。按目標分組：

**調試器。** 內核調試器檢查（`52F`）、SoftICE/Syser 時代檢查（`BE0`），以及嵌在加載器代碼中的計時敏感誘餌（見下文）。VMware 後門探測（`540`）同時充當模擬器檢查：`in eax, dx` 後門指令在真實硬件與多數模擬器上出錯，但在 VMware 下返回一個魔數。

**虛擬機。** 註冊表字符串檢查（`A09`），針對三個值——`HKLM\Hardware\Description\System\SystemBiosVersion`、`HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation\SystemProductName` 與 `HKLM\Hardware\Description\System\BIOS\SystemProductName`——在值的開頭匹配：`Virtual`、`VMware`、`Bochs`、`VBOX`、`VRTUAL`、`Microsoft Hyper-V`、`Parallels`。同一階段有時檢查 CPU 特性標誌（要求硬件虛擬化暴露給客戶機）。

**系統完整性。** OS 最低/兼容版本檢查（`C00`/`B00`）、針對 `testsigning` 或 `disableintegritychecks` 的啟動選項檢查（`C01`，它會擋住常見的未簽名驅動分析環境），以及確保 `C:\Windows\msc.log.log` 不存在的檢查（`BD0`）。

**進程完整性。** 注入 DLL 清掃（`A0F`）、先殺（`A07`）再在殘留時中止（`A01`）的注入線程清掃、父進程策略（`A03`），以及——對受保護 DLL——宿主進程檢查（`A11`），尋找宿主中保護器自身的標記。`A07` 清掃決定了進程內分析輔助代碼要麼在此之前運行、要麼睡過它。

**反鉤子。** 在 `A08`/`A04`，加載器把磁盤上純淨系統 DLL 中 ntdll/kernel32 的*代碼*拷入內存並優先使用之，挫敗對這些模塊的用戶態內聯鉤子；`A04` 在磁盤映像本身被補丁時中止。

