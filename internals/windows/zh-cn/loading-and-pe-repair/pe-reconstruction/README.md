---
description: "重建 PE 节表头、入口点、数据目录、导入表、TLS、导出表、重定位与 CLR 元数据。"
icon: puzzle-piece
---

# PE 重建

节数据恢复完成后，会得到一块按 RVA 索引的内存缓冲区（共 `SizeOfImage` 字节）。要将该缓冲区还原为合法、可加载的 PE 文件，需要根据对应构建所属的布局族系，修复被清空或重定向的头部字段、导入表、TLS 状态、导出表、基址重定位、`.text` 页混淆以及 CLR 元数据。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-memory"></i></td><td><strong>头部、节表与零填充区间</strong></td><td>按 RVA 映射的节表头、32 位文件紧缩、临时解密的入口点与数据目录块，以及 <code>.bss</code> 零填充链表。</td><td><a href="memory-image.md">头部、节表与零填充区间</a></td></tr><tr><td><i class="fa-sitemap"></i></td><td><strong>导入表、TLS 与导出表</strong></td><td>按布局族系区分的导入表恢复、<code>.kmiat</code> 重建、TLS 还原与重定位项修复，以及从桩 PE 回拷导出表。</td><td><a href="imports-tls-exports.md">导入表、TLS 与导出表</a></td></tr><tr><td><i class="fa-cubes"></i></td><td><strong>重定位、页面变换与 CLR 数据</strong></td><td><code>/FIXED</code> 与 ASLR 重定位策略、<code>.text</code> 页混淆执行顺序，以及按字段精确覆盖的 CLR 元数据还原。</td><td><a href="relocations-managed.md">重定位、页面变换与 CLR 数据</a></td></tr></tbody></table>
