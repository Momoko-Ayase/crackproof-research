---
description: "运行期启动流程、状态码、反分析检测、按需页解密保护、辅助模块与 Htsysm 驱动。"
icon: play
---

# 运行时行为

受保护的 Windows 程序在运行时会先执行 CrackProof 的引导加载器，最后在状态 `280` 跳转到原始入口点（OEP）。在此期间，加载器按配置打开可选调试日志，在内存中手动映射辅助 DLL，依次检查操作系统、虚拟机、调试器与进程环境，按需初始化 `Htsysm` 内核驱动，重建各节与导入表，并可配合 `KiUserExceptionDispatcher` hook 对可执行页面重新加密保护。

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-list-ol"></i></td><td><strong>启动流程与状态上报</strong></td><td>12 位十六进制启动状态码、<code>%temp%</code> 下的 12 位十六进制目录开关、<code>ErrLog-Pec</code> 邮槽与 <code>AAA-BBB-CCC</code> 错误码。</td><td><a href="startup-status.md">启动流程与状态上报</a></td></tr><tr><td><i class="fa-user-shield"></i></td><td><strong>环境与反分析检测</strong></td><td>调试器、虚拟机、启动项、注入 DLL 与外部线程、<code>A11</code>/<code>A15</code> 宿主校验及系统 DLL 反 Hook。</td><td><a href="environment-checks.md">环境与反分析检测</a></td></tr><tr><td><i class="fa-lock"></i></td><td><strong>页面保护与加载器代码</strong></td><td>基于 <code>KiUserExceptionDispatcher</code> 的按需页解密、<code>scribble</code> 涂抹、多态变形、诱饵指令与磁盘自映射。</td><td><a href="page-protection.md">页面保护与加载器代码</a></td></tr><tr><td><i class="fa-layer-group"></i></td><td><strong>手动映射辅助模块</strong></td><td>内嵌辅助 DLL（<code>it</code>、<code>dt</code>、<code>cm</code>、<code>dm</code>、<code>sk</code>、<code>pm</code>）的职责分工及其规避 PEB 模块链表的机制。</td><td><a href="mapped-modules.md">手动映射辅助模块</a></td></tr><tr><td><i class="fa-gears"></i></td><td><strong>Htsysm 内核组件</strong></td><td>第一至第三代驱动演进（<code>Htsysm</code>、<code>Htsysm7679</code>，以及含 <code>Htsysm1B4001</code> 在内的 <code>0xAA02</code> <code>ObRegisterCallbacks</code> 驱动）。</td><td><a href="kernel-components.md">Htsysm 内核组件</a></td></tr></tbody></table>
