---
description: "自我解密的載入器階段鏈、各類版型變體與試探驗證如何還原受保護區段。"
icon: stairs
---

# 載入與區段還原

受保護的 Windows 容器串接了五至八層自我解密的載入器階段；各階段金鑰依賴前序 CRC-32 校驗和、三角級數金鑰推進與隨組建生成的位元組碼存根，全部解開後才能取得最終的區段還原資料表。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-link"></i></td><td><strong>階段鏈與標記版型</strong></td><td>複合式階段解密流程，以及 64 位元帶標記版型的九步驟還原管線。</td><td><a href="stage-chain.md">階段鏈與標記版型</a></td></tr><tr><td><i class="fa-code-branch"></i></td><td><strong>PE32、專用 DLL 與無標記版型</strong></td><td>標準型與精簡型 PE32 外殼、64 位元專用 DLL 固定資料表，以及無標記 64 位元結構探索。</td><td><a href="layout-variants.md">PE32、專用 DLL 與無標記版型</a></td></tr><tr><td><i class="fa-magnifying-glass"></i></td><td><strong>結構探索與驗證</strong></td><td>試解密、壓縮區塊驗證，以及 <code>.text</code> 分頁擾碼模式的選擇規則。</td><td><a href="discovery-validation.md">結構探索與驗證</a></td></tr></tbody></table>
