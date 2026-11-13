---
description: "对 CrackProof 保护格式与运行时机制的独立技术研究。"
icon: house
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

# CrackProof 技术研究

CrackProof® 是 HyperTech 推出的商业二进制保护系统系列。本站记录了经独立验证的文件格式、数据变换、分阶段加载器及运行时组件细节。

研究内容涵盖 Windows PE 文件（CrackProof for Windows®）与 Android AArch64 共享库。两个平台的容器格式与还原流程彼此独立，内部机制分设专章说明。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-desktop"></i></td><td><strong>Windows 内部机制</strong></td><td>受保护 PE 布局、加密算法、分阶段加载、PE 重建与运行时检查。</td><td><a href="https://app.gitbook.com/s/fEb9nKPvKsjkPAHMUbOt/">CrackProof for Windows® 内部机制</a></td></tr><tr><td><i class="fa-mobile-screen-button"></i></td><td><strong>Android SO 内部机制</strong></td><td>受保护 AArch64 ELF 布局、嵌套模块流、容器解码、ELF 还原与 IL2CPP 元数据。</td><td><a href="https://app.gitbook.com/s/Aoyn9wKiHAVzBKGSUifa/">CrackProof Android SO 内部机制</a></td></tr><tr><td><i class="fa-code"></i></td><td><strong>验证与参考实现</strong></td><td>Windows 数据变换的测试向量、可运行的 Python 参考实现与脱敏调试日志。</td><td><a href="https://app.gitbook.com/s/L9bXLua8yrIPEUZOHO21/">验证与参考实现</a></td></tr><tr><td><i class="fa-screwdriver-wrench"></i></td><td><strong>Senbei</strong></td><td>面向受保护 Windows PE、Android 共享库与 IL2CPP 元数据的静态脱壳工具：CLI、桌面 GUI、架构设计与开发指南。</td><td><a href="https://app.gitbook.com/s/tMIkyJzuS8q10cZToDDD/">Senbei</a></td></tr><tr><td><i class="fa-shield-halved"></i></td><td><strong>Arare</strong></td><td>从源码构建、复现已知布局族的 Windows PE 加壳器：CLI、GUI、支持矩阵、架构设计与开发指南。</td><td><a href="https://app.gitbook.com/s/WU1t9Kr3H23IyrF4AqbS/">Arare</a></td></tr></tbody></table>

## 研究范围

文中记录的每项规则均来自可观测的二进制结构与运行时行为。字段和组件命名优先沿用二进制内置字符串、调试日志输出与平台标准规范；无现成名称时，直接按字节的实际作用命名。仅当多个样本存在共性，或二进制内部的一致性校验强制要求时，才将某项行为归纳为格式通则。

研究章节均隐去了受保护产品名称、特定部署的驱动文件名及可识别样本来源的路径。Senbei 与 Arare 则在各自独立的产品章节中说明。

{% hint style="warning" %}
**法律声明。** 请仅对您拥有所有权或已获明确授权分析的二进制文件使用本资料。不同司法管辖区对规避技术保护措施的法律规定及许可协议要求各不相同。本文档为独立技术研究，不包含任何厂商源码或密钥，与 HyperTech 无关，亦不授权重新分发还原后的二进制文件。
{% endhint %}
