---
description: CrackProof 保护格式与运行时行为的独立技术研究。
layout:
  width: wide
  title:
    visible: true
  description:
    visible: true
  tableOfContents:
    visible: false
  outline:
    visible: false
  pagination:
    visible: false
  metadata:
    visible: false
  tags:
    visible: true
  actions:
    visible: false
---

# CrackProof 研究

CrackProof® 是 HyperTech 开发的一系列商用二进制保护系统。本站记录通过独立分析验证的文件格式、数据变换、加载器与运行时组件。

当前研究范围包括 Windows PE 文件和 Android 原生库。两个平台使用不同的容器格式与恢复路径，因此分别编写内部机制文档。

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><strong>Windows 内部机制</strong></td><td>受保护 PE 布局、数据变换、分阶段加载、PE 重建与运行时行为。</td><td><a href="https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/">CrackProof for Windows 内部机制</a></td></tr><tr><td><strong>Android SO 内部机制</strong></td><td>受保护 AArch64 ELF 布局、模块流、容器解码、ELF 恢复与 IL2CPP 元数据。</td><td><a href="https://app.gitbook.com/s/Aoyn9wKiHAVzBKGSUifa/">CrackProof for Android SO 内部机制</a></td></tr><tr><td><strong>验证与参考</strong></td><td>文中 Windows 数据变换的可执行测试向量与小型参考实现。</td><td><a href="https://app.gitbook.com/s/L9bXLua8yrIPEUZOHO21/">验证与参考</a></td></tr></tbody></table>

## 研究边界

文档只描述可观察的结构与行为。名称来自二进制、日志、已有平台术语，或对字段作用的直白说明。只有经过多个样本验证，或能通过内部一致性约束证明的结论，才会写成格式行为。

文档不记录受保护产品名称、部署专用驱动名和可识别样本的信息。用于验证研究结论的实现项目名称不作为公开术语。

## 法律声明

仅可将这些信息用于您拥有或已获明确授权分析的二进制。各司法辖区的规避限制与许可条款不同。本文档是独立研究成果，不包含厂商源代码或密钥，与 HyperTech 无隶属关系，也不授权再分发恢复后的二进制。
