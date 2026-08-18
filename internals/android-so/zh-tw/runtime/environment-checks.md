---
description: "加載時已觀察的 Android 環境、完整性與轉儲相關檢查。"
---

# 環境與完整性檢查

Windows 構建把用戶態探測與可選的內核支持疊在一起。Android 家族留在用戶態。下面的檢查來自第一階段、第二階段，以及[運行時模塊](modules.md)列出的模塊。它們在洋蔥仍在物化時運行，而不是在已恢復的 ELF 就位之後。

## 進程與翻譯環境

第一階段已經遍歷 `/proc/self/maps` 以找到自己的文件。第二階段保留 maps 上下文，並查看 `/proc/self/environ`。一種已觀察探測通過陳述 `/system/lib/libhoudini.so` 與 `/system/lib64/arm64/nb/` 下的路徑，測試是否存在 x86-on-ARM 翻譯層。正在翻譯 ARM 代碼、而不是原生跑 AArch64 的宿主，因此與加載器所期望的環境不同。

模塊 `0x8F` 讀 `/proc/self/cmdline`，查詢 uid/gid/tid，並檢查某路徑的屬主與模式。模塊 `0x60` 掃描系統庫目錄、進程環境與運行時路徑。模塊 `0x20` 校驗目標路徑、ELF 頭、`/proc/self/maps` 以及 libc 映射。

## 第二進程與 ptrace

已觀察的 IL2CPP 庫在 ART 啟動且 VM 模塊映射之後、受保護庫本身加載之前，fork 一個輔助進程。子進程用 `PTRACE_SEIZE` 與 `PTRACE_O_EXITKILL` 抓住父進程。這佔住 ptrace 槽位，並把兩個進程的壽命綁在一起。因此子進程的 maps 裡不會出現受保護庫。

## 內存可見性

打開並讀取 `/proc/<pid>/mem` 已被觀察到會在數秒內殺死進程。讀 `maps`、`cmdline` 與 `status` 則不會。同一批構建上 `process_vm_readv` 沒有引起這種反應。恢復完成後，可執行頁保持可讀——沒有 Windows 那種對按需出錯代碼做 `PAGE_NOACCESS` 再加密。

## 包與時間

模塊 `0x40` 檢查 `base.apk` 與同級拆分 APK。已觀察的簽名順序是 v3.1，然後 v3，然後 v2，然後 JAR/v1。模塊 `0x02` 發送 UDP 123 端口時間查詢，並把答覆與配置閾值比較。模塊 `0x69` fork 一個子探測並等待其退出狀態。

## 缺席的部分

這條路徑上沒有 Htsysm 一類內核驅動。第二階段模塊是普通用戶態映像，常常落在私有 RWX 區域，運行後可以擦掉或改寫自己。它們不出現在動態鏈接器的模塊列表裡，與 Windows 上[手動映射的輔助模塊](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/runtime/mapped-modules)造成的缺口同類。
