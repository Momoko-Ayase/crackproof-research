---
description: "多阶段自解密加载器链、各布局分支与试探校验如何还原受保护的节数据。"
icon: stairs
---

# 加载流程与节还原

加壳后的 Windows 容器串联了五至八个自解密加载器阶段；各阶段密钥依次依赖前序阶段的 CRC-32 校验和、三角和密钥步进以及按构建生成的字节码存根，逐级解密后得到最终的节还原描述符表。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-link"></i></td><td><strong>阶段链与有标记布局</strong></td><td>复合阶段解密流程，以及 64 位有标记布局的九阶段节还原流水线。</td><td><a href="stage-chain.md">阶段链与有标记布局</a></td></tr><tr><td><i class="fa-code-branch"></i></td><td><strong>PE32、DLL 与无标记布局</strong></td><td>标准与紧凑 PE32 壳体、专用 64 位 DLL 固定偏移表，以及无标记 64 位构建的结构定位。</td><td><a href="layout-variants.md">PE32、DLL 与无标记布局</a></td></tr><tr><td><i class="fa-magnifying-glass"></i></td><td><strong>结构定位与试探校验</strong></td><td>试探解密、压缩块解压验证，以及 <code>.text</code> 页面混淆模式的判定规则。</td><td><a href="discovery-validation.md">结构定位与试探校验</a></td></tr></tbody></table>
