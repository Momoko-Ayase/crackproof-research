---
description: "实战逆向分析流程、保护机制局限性、-GMD IL2CPP 元数据还原与常量速查表。"
icon: compass
---

# 分析要点

分析受 CrackProof 保护的 Windows 程序时，通常要结合静态结构校验、调试日志状态码到阶段代码的映射，以及针对特定格式的还原后校验。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-check"></i></td><td><strong>分析流程</strong></td><td>开启调试日志、定位阶段代码、转储按需页加密模块及静态校验还原后 PE 的分步流程。</td><td><a href="workflow.md">分析流程</a></td></tr><tr><td><i class="fa-triangle-exclamation"></i></td><td><strong>已知设计局限</strong></td><td>虚拟机检测、调试日志、按需缺页解密、内核驱动与无密钥校验链中可复现的架构局限。</td><td><a href="observed-limitations.md">已知设计局限</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>il2cpp 元数据混淆</strong></td><td>还原 Unity IL2CPP Windows 构建中无需密钥的 <code>-GMD</code> 稀疏 MethodDef Token 重映射。</td><td><a href="il2cpp-metadata.md">il2cpp 元数据混淆</a></td></tr><tr><td><i class="fa-sliders"></i></td><td><strong>常量与偏移速查</strong></td><td>文件魔数、容器计算公式、加解密与校验计算式、PE32/PE32+ 字段偏移及字节码操作码汇总表。</td><td><a href="constants.md">常量与偏移速查</a></td></tr></tbody></table>
