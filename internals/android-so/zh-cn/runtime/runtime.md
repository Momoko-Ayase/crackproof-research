---
description: "从第一阶段 .init_array 桩到嵌套第二阶段解释器与环境探测的加载期流程。"
icon: play
---

# 运行时

加载时，Android 动态链接器映射被挖空的 ELF 并执行 `.init_array`，首先进入第一阶段引导桩。第一阶段映射并解密第二阶段（`0xE2`），第二阶段分配 256 槽模块表，逐层执行嵌套解释器流（`0xE2`..`0xE8`），执行用户态环境与完整性检查，还原内存中的 ELF 加载段与重定位表，最后通过模块 `0x98` 调起原始构造函数。

静态恢复只需提取容器、符号、重定位、构造函数与元数据相关模块（`0x9B`、`0x9D`、`0x9E`，外加可选的 `0x96`、`0x98` 与 `0x0C`）；环境检查模块仅在运行时执行。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-bolt"></i></td><td><strong>第一阶段引导</strong></td><td>通过 <code>/proc/self/maps</code> 自定位、<code>SHT_LOUSER</code> 解密、页大小探测与寄存器移交。</td><td><a href="stage1-bootstrap.md">第一阶段引导</a></td></tr><tr><td><i class="fa-microchip"></i></td><td><strong>第二阶段解释器</strong></td><td>256 槽模块表、<code>0x5C</code> 记录描述符，以及逐层嵌套的 <code>0xE2</code>..<code>0xE8</code> 流解释过程。</td><td><a href="stage2-interpreter.md">第二阶段解释器</a></td></tr><tr><td><i class="fa-user-shield"></i></td><td><strong>环境与完整性检查</strong></td><td>NativeBridge 检测、<code>PTRACE_SEIZE</code> 守护子进程、<code>/proc/&lt;pid&gt;/mem</code> 读取检测与 APK 签名校验。</td><td><a href="environment-checks.md">环境与完整性检查</a></td></tr><tr><td><i class="fa-layer-group"></i></td><td><strong>运行时模块</strong></td><td>已观测到的第二阶段模块 ID 汇总，涵盖流解释器、映像恢复与环境检查模块。</td><td><a href="modules.md">运行时模块</a></td></tr></tbody></table>
