---
description: "提取第二阶段模块产物，重建动态链接表，并输出干净的 ELF64 共享库。"
icon: puzzle-piece
---

# 恢复

静态恢复分为两个阶段：先从 `SHT_LOUSER` 私有节中提取第二阶段模块集合，再重建 ELF 加载段、动态链接表与节表，并在输出后完成校验。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-route"></i></td><td><strong>模块流</strong></td><td>必需的基础模块（<code>0x9B</code>、<code>0x9D</code>、<code>0x9E</code>）与可选静态模块（<code>0x96</code>、<code>0x98</code>、<code>0x0C</code>）。</td><td><a href="module-streams.md">模块流</a></td></tr><tr><td><i class="fa-link"></i></td><td><strong>动态链接</strong></td><td>隐藏符号还原、<code>0x96</code> 符号下标逆置换、省略的 <code>libc</code> PLT 槽位修补、构造函数恢复与 <code>PT_LOAD</code> 布局。</td><td><a href="dynamic-linking.md">动态链接</a></td></tr><tr><td><i class="fa-file-export"></i></td><td><strong>ELF 输出</strong></td><td>剥离 <code>SHT_LOUSER</code>、清零 <code>e_entry</code>、重排非加载节文件偏移，以及硬性错误与结构诊断校验。</td><td><a href="elf-output.md">ELF 输出</a></td></tr></tbody></table>
