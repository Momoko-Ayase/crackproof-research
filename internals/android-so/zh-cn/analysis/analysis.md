---
description: "失败即中止的结构校验清单与已观测到的 Android 共享库格式常量。"
icon: compass
---

# 分析

ELF 识别、第一阶段与第二阶段解密、动态表重建以及 IL2CPP 元数据还原，都会在进入下一阶段前校验结构边界。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-check"></i></td><td><strong>校验清单</strong></td><td>覆盖格式识别、数据流提取、ELF 重建与元数据的按序结构校验。</td><td><a href="validation.md">校验清单</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>常量</strong></td><td>已观测到的魔数、偏移量、密码算法常量与模块 ID 汇总表。</td><td><a href="constants.md">常量</a></td></tr></tbody></table>
