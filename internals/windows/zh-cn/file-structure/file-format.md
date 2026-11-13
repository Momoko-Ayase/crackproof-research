---
description: "磁盘容器布局、KONN 头部识别、构建类型分类与外部伴生文件切分。"
icon: folder-tree
---

# 受保护文件结构

加壳后的 Windows 二进制文件在前 `0x1000` 字节保留可正常加载的外层 PE 头部，偏移 `0x1000` 处存放加密参数头，其后紧跟多阶段加载器与压缩后的应用节数据（或拆分至同目录下的 `._` 伴生文件）。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-box-archive"></i></td><td><strong>容器布局与加密头部</strong></td><td>固定的 <code>0x1000</code> 切分边界、8 双字 <code>info</code> 头部密钥派生算法与载荷搬运范围。</td><td><a href="container-layout.md">容器布局与加密头部</a></td></tr><tr><td><i class="fa-fingerprint"></i></td><td><strong>识别与构建类型</strong></td><td>基于文件内容的 <code>KONN</code> 特征识别、PE32 与 PE32+ CLR 模块分类，以及各布局分支。</td><td><a href="recognition.md">识别与构建类型</a></td></tr><tr><td><i class="fa-copy"></i></td><td><strong>节数据与伴生文件</strong></td><td><code>0x1080</code> 处按位取反编码的节数据基址，以及外部 <code>._</code> 伴生文件的配对与覆盖规则。</td><td><a href="companion-layout.md">节数据与伴生文件</a></td></tr></tbody></table>
