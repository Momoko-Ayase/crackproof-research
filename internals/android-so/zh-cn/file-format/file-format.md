---
description: "识别受保护的 Android ELF64 共享库，定位第一阶段与第二阶段载荷边界。"
icon: folder-tree
---

# 文件格式

受保护的 Android 共享库本身仍是合法的小端序 ELF64 AArch64 二进制文件。动态链接相关各节在节表中保持可见，可加载的代码与数据段则被原位清零，原始载荷移入文件末尾唯一的 `SHT_LOUSER` 私有节中。

格式识别执行严格校验：头部类型、节文件偏移、参数范围以及嵌套流边界必须全部吻合，任一检查不通过即予拒绝。运行时如何在内存中定位这些结构见[第一阶段引导](../runtime/stage1-bootstrap.md)。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-file-code"></i></td><td><strong>受保护 ELF</strong></td><td>必需的 ELF64 头部、动态链接节、<code>.init_array</code> 引导槽位与 APK 附带文件。</td><td><a href="protected-elf.md">受保护 ELF</a></td></tr><tr><td><i class="fa-box-archive"></i></td><td><strong>第一阶段头部</strong></td><td><code>SHT_LOUSER</code> 载荷节布局、32 字节参数头与相对偏移边界检查。</td><td><a href="stage1.md">第一阶段头部</a></td></tr><tr><td><i class="fa-bars-staggered"></i></td><td><strong>第二阶段记录流</strong></td><td><code>0x5C</code> 字节记录描述符、直接切片与子流分支，以及容器载荷分发。</td><td><a href="stage2-streams.md">第二阶段记录流</a></td></tr></tbody></table>
