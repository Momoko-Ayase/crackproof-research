---
description: "控制權到達原程序前執行的用戶態與內核輔助檢查。"
---

# 環境與反分析檢查

檢查在解密之前（部分與解密交錯）運行。按目標分組：

**調試器。** 用戶態檢查從 `410` 開始，包括 `IsDebuggerPresent` 和 `NtQueryInformationProcess`（`520`）。另外還有內核調試器檢查（`52F`）、SoftICE/Syser 時代檢查（`BE0`），以及[頁保護與加載器代碼](page-protection.md#加載器自身的代碼多態與誘餌)中計時敏感的誘餌。VMware 後門探測（`540`）同時充當模擬器檢查：`in eax, dx` 後門指令在真實硬件與多數模擬器上出錯，但在 VMware 下返回一個魔數。OS 版本檢查（`C00`）讀的是真實版本；把 PEB 裡的 OS 版本字段改成更低的值會在 `C00` 失敗。

**虛擬機。** 註冊表字符串檢查（`A09`）針對三個值（`HKLM\Hardware\Description\System\SystemBiosVersion`、`HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation\SystemProductName` 與 `HKLM\Hardware\Description\System\BIOS\SystemProductName`），在值的開頭匹配：`Virtual`、`VMware`、`Bochs`、`VBOX`、`VRTUAL`、`Microsoft Hyper-V`、`Parallels`。同一階段有時檢查 CPU 特性標誌（要求硬件虛擬化暴露給客戶機）。

**系統完整性。** OS 最低/兼容版本檢查（`C00`/`B00`）、針對 `testsigning` 或 `disableintegritychecks` 的啟動選項檢查（`C01`，它會擋住常見的未簽名驅動分析環境），以及確保 `C:\Windows\msc.log.log` 不存在的檢查（`BD0`）。部分 `1B40` 家族構建還會把正在運行的驅動設備名和一份短名單比較（`E55`、`E91`）。

**進程完整性。** 注入 DLL 清掃（`A0F`）已觀察會查看 `AppInit_DLLs`、`user32.dll`、`apphelp.dll` 和 `ShimEng.dll`；先殺（`A07`）再在殘留時中止（`A01`）的注入線程清掃；父進程策略（`A03`）；以及，對受保護 DLL，宿主進程檢查（`A11`）。部分宿主可執行文件還會拒絕自己目錄裡多出來的 DLL。`A07` 清掃決定了進程內分析輔助代碼要麼在此之前運行、要麼睡過它。

`A11` 讀取宿主可執行文件的已映射映像（受保護 DLL 與宿主同一進程），尋找保護器自身的標記：掃描節表中名為 `peC` 的節，並在導入表中查找以精確大小寫 `KeRnEl32.dLl` 導入的模塊（奇怪的大小寫本身就是標記——正常導入不區分大小寫，所以殼可以隨便拼寫）。兩個標記任一命中即可通過。該檢查還有一個帶額外標誌參數的變體。宿主兩個標記都沒有的 DLL 會在記錄 `A15` 之前就中止啟動。

`A15` 是標記而非檢查：它沒有自己的代碼體。檢查調度器在受保護 DLL 那一趟（`5D0` 之後）按構建選項位發出它。在日誌裡它緊跟宿主進程驗證（`A09`、`A11`）之後，所以它出現即表示 DLL 接受了宿主、啟動進入解密前奏。宿主可執行文件從不記錄 `A15`；宿主日誌中同一位置是 `552`/`570`。

**反鉤子。** 在 `A08`/`A04`，加載器把磁盤上純淨系統 DLL 中 ntdll/kernel32 的*代碼*拷入內存並優先使用之，挫敗對這些模塊的用戶態內聯鉤子；`A04` 在磁盤映像本身被補丁時中止。

