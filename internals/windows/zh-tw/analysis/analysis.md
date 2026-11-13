---
description: "實務分析流程、架構限制、-GMD IL2CPP 中繼資料重映射與常數參考表。"
icon: compass
---

# 分析筆記

對受 CrackProof 保護的 Windows 二進位檔進行靜態與執行期分析時，主要仰賴結構交叉比對、將除錯記錄碼對應至各階段常式，以及針對重建結果檢查各項格式不變條件。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-check"></i></td><td><strong>分析流程</strong></td><td>逐步說明如何啟用除錯記錄、定位各階段常式、傾印受分頁保護的模組並驗證 PE 輸出。</td><td><a href="workflow.md">分析流程</a></td></tr><tr><td><i class="fa-triangle-exclamation"></i></td><td><strong>實測架構限制</strong></td><td>涵蓋 VM 檢查、除錯記錄、隨選分頁、驅動程式與 CRC 檢查鏈中可重現的設計限制。</td><td><a href="observed-limitations.md">實測架構限制</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>il2cpp 中繼資料混淆</strong></td><td>還原 Unity IL2CPP 組建中無須金鑰的 Windows <code>-GMD</code> 稀疏 MethodDef token 混淆。</td><td><a href="il2cpp-metadata.md">il2cpp 中繼資料混淆</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>常數與偏移</strong></td><td>彙整魔術數值、容器計算公式、PE32/PE32+ 欄位偏移與位元組碼運算碼的總覽表。</td><td><a href="constants.md">常數與偏移</a></td></tr></tbody></table>
