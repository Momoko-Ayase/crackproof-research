---
description: "Android 使用者空間的反分析、NativeBridge、ptrace、記憶體與 APK 簽章檢查。"
icon: user-shield
---

# 環境與完整性檢查

不同於 Windows 產品線，Android 上的 CrackProof 完全在使用者空間運作，不依賴核心驅動程式。各類偵測邏輯分散在 Stage 1、Stage 2 與 [執行階段模組](modules.md) 所列的工作模組中，在巢狀串流解開的同時一併執行。

## 行程與 ABI 轉譯檢查

* **自身映射與環境變數：** Stage 1 會解析 `/proc/self/maps` 以定位底層 ELF 檔案；Stage 2 則會保留映射資訊並檢查 `/proc/self/environ`。
* **ARM-on-x86 二進位轉譯（NativeBridge）：** 偵測常式會檢查 `/system/lib/libhoudini.so` 與 `/system/lib64/arm64/nb/` 是否存在，藉此判斷環境是否透過 ARM-on-x86 轉譯層執行而非原生 AArch64。
* **檔案系統與 libc 檢查：** 模組 `0x8F` 會檢查 `/proc/self/cmdline`、`uid`/`gid`/`tid` 以及檔案擁有者與權限；模組 `0x60` 會掃描系統程式庫資料夾與執行期路徑；模組 `0x20` 則驗證目標 ELF 標頭、`/proc/self/maps` 以及目前生效的 `libc` 映射。

## 輔助行程與 `PTRACE_SEIZE`

在已觀測的 IL2CPP 組建中，應用程式會在 ART 與虛擬機器程式庫初始化完成後、`dlopen` 載入受保護 `.so` 之前，先 `fork` 出一個輔助行程。子行程會以 `PTRACE_SEIZE | PTRACE_O_EXITKILL` 附加至父行程，占住核心的 `ptrace` 附加槽位，且只要任一方行程結束就會一併終止應用程式。由於 `fork` 發生在受保護 `.so` 載入之前，該程式庫不會出現在 `/proc/<child>/maps` 中。

## `/proc/<pid>/mem` 監控與頁面權限

在已觀測的組建上，開啟並讀取 `/proc/<pid>/mem` 會在數秒內導致行程終止；但讀取 `/proc/<pid>/maps`、`cmdline` 或 `status`，或是透過 `process_vm_readv` 讀取記憶體，在這些組建上都不會觸發終止。當 `0x9B` 完成程式區段還原後，可執行頁面會維持可讀狀態（`PROT_READ | PROT_EXEC`）；Android 組建並未安裝基於 `PAGE_NOACCESS` 缺頁例外（demand-fault）的單頁即時解密機制。

## APK 簽章與網路時間

模組 `0x40` 會由高至低依序驗證 `base.apk` 與 split APK 的簽章格式：先檢查 APK Signature Scheme v3.1，接著為 v3、v2，最後為 JAR 簽章（v1）。模組 `0x02` 會透過 UDP 連接埠 123 向 NTP 伺服器查詢時間，並比對回傳時間戳記是否落在設定範圍內。模組 `0x69` 則會建立短暫存在的偵測用子行程，並檢查 `wait` 回傳的結束狀態。

## 不留存於連結器模組清單

Stage 2 各層直譯器與工作模組皆位於匿名 `mmap` 記憶體區域（初始化期間常為 `RWX`），且在回呼函式執行完畢後可將自身清零或覆寫。如同 Windows 上的 [手動映射輔助 DLL](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/runtime/mapped-modules)，這些模組都不會出現在 Bionic 的 `dl_iterate_phdr` 或 `soinfo` 串列中。
