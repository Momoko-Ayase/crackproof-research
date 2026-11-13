---
description: "Android IL2CPP 元数据的方法令牌与 methodIndex 置换及存储布局。"
icon: database
---

# 元数据

在 Unity IL2CPP 的 Android 构建中，CrackProof 会连同 `libil2cpp.so` 一起保护 `global-metadata.dat`。具体方式取决于元数据版本与打包形态：一种是对外部 `global-metadata.dat` 文件中的方法令牌或 `methodIndex` 字段执行置换（运行时由模块 `0x0C` 的 `mmap` hook 还原）；另一种是用一组 32 位 XOR 密钥封装精简版 v24 元数据块，嵌入 `.so` 的数据节中。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-hashtag"></i></td><td><strong>方法令牌</strong></td><td>29、31、39 版的五轮逆置换、v31 按表顺序回退重映射，以及 24.1 版 <code>methodIndex</code> 还原。</td><td><a href="method-tokens.md">方法令牌</a></td></tr><tr><td><i class="fa-table"></i></td><td><strong>存储布局</strong></td><td>外部 <code>global-metadata.dat</code> 配对规则与内嵌 XOR 封装精简版 v24 元数据块。</td><td><a href="storage-layouts.md">存储布局</a></td></tr></tbody></table>
