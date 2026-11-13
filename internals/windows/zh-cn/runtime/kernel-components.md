---
description: "三代 Htsysm 驱动演进：内核执行、EPROCESS 改写与句柄权限过滤。"
icon: gears
---

# Htsysm 内核组件

CrackProof 的可选内核保护层（`Htsysm`）先后演进出三代截然不同的驱动架构：

{% tabs %}
{% tab title="第 1 代：HtsysmNT" %}
### 未鉴权的内核 Shellcode 执行

第 1 代驱动暴露了一个无调用方鉴权的 IOCTL，可直接在 Ring 0 执行调用方传入的 Shellcode。CrackProof 的用户态辅助模块 `cm` 利用这一原语手动映射两个内核态 DLL（状态 `B21` 加载 `HtsyskNT.dll`，状态 `BB0` 加载 `HtpecmNT.dll`），并调用其导出的 `_FarEntry@0` 完成内核内存读写与进程终止。由于该 IOCTL 不校验调用方身份，一旦加载该驱动，本机任意进程都可借此在 Ring 0 执行任意代码。
{% endtab %}

{% tab title="第 2 代：Htsysm7679" %}
### 受边界限制的 `EPROCESS` 掩码双字改写（`0xAA01`）

第 2 代驱动（`Htsysm7679`，设备类型 `0xAA01`，IOCTL 为 `0xAA013880` / `0xAA013884` / `0xAA013888`）移除了通用 Shellcode 执行能力，改为在无符号偏移满足 `offset < 0x1000` 的范围内，对 `IoGetCurrentProcess() + offset` 执行按掩码的 32 位清位、置位或读取操作。

* **受保护进程（`PP`）开关：** 在阶段 `C03`/`C04`，加载器置位当前进程 `EPROCESS` 中的受保护进程（Protected Process）位域，阻止用户态调试器和注入器打开完全访问权限句柄。由于开启 `PP` 会导致部分 Win32/NT 调用（如 `NtCreateSection`）失败，用户态加载器会在 `C04` hook 这些函数，调用前先清除 `PP`，调用原 API 后再重新置位 `PP`。
* **BYOVD 攻击面：** 调用方校验仅依赖基于 PID 的可逆变换，本机任意进程只要复现该变换，即可改写自身 `EPROCESS` 内 `offset < 0x1000` 范围的字段，也可趁目标进程尚未在 `C04` 激活 `PP` 前提前完成注入。
{% endtab %}

{% tab title="第 3 代：Htsysm767901 与 Htsysm1B4001" %}
### 基于 `ObRegisterCallbacks` 的句柄权限过滤（`0xAA02`）

第 3 代驱动（`Htsysm767901` 与 `Htsysm1B4001`，设备类型 `0xAA02`，共 12 个 IOCTL `0xAA023800..0xAA02382C`）彻底取消了 `EPROCESS` 直接改写，改向对象管理器注册回调（`ObRegisterCallbacks`；`Htsysm1B4001` 上的回调 Altitude 为 `88180.011104000001`，由 `1B4001` 派生），最多同时跟踪 100 个受保护进程并维护一个 12 项遥测环形缓冲区。

* **剥离访问掩码（`& 0xFFFFFFC5`，清除 `0x3A`）：** 对未经豁免的句柄打开或复制请求，剥离 `PROCESS_CREATE_THREAD`（`0x02`）、`PROCESS_VM_OPERATION`（`0x08`）、`PROCESS_VM_READ`（`0x10`）与 `PROCESS_VM_WRITE`（`0x20`）四项权限。
* **豁免规则：** 放行内核句柄（`KernelHandle`）、进程自访问、最多 5 个预配置的调用方 PID（`0xAA02380C`）、最多 3 个预配置的调用方父进程 PID（`0xAA023810`），以及**仅限从预配置系统目录启动的** `csrss.exe`、`lsass.exe`、`conhost.exe` 或 `svchost.exe`（`0xAA023800`，其中 `svchost.exe` 还需匹配预期的父进程 PID `0xAA023814`）。
* **三态注册握手：** 受保护进程接入时基于自身代码与返回地址哈希完成握手，不再使用静态 PID 变换，也不向用户态调用方提供任何内核写原语。
{% endtab %}
{% endtabs %}

## 版本印记（`0x7679` 与 `1B40`）

`Htsysm7679` / `Htsysm767901` 名称中的 `0x00007679`，与 PE32 `EighthStage` 及 64 位 Stage 5 标记表中的 `0x00007679` 配置簇印记一致（详见 [PE32、DLL 与无标记布局](../loading-and-pe-repair/loading/layout-variants.md)）。较新的 Windows 构建在 `C02`/`C03` 记录 `Htsysm1B4001`，与 Android 版本共用 `1B40` 版本印记，统一采用第 3 代 `0xAA02` 回调驱动（`C04` 阶段所需的用户态 API hook 也随之减少），并经常同时启用 `E` 系列设备检查（`E55`、`E91`）。

## 组件汇总表

| 组件 | 所在层级 | 职责 |
| --- | --- | --- |
| `HtpecIt.dll`（`it`） | 手动映射的用户态 DLL | `Axx` 防篡改、反注入、虚拟机与宿主进程检测 |
| `HtdpStub2.dll`（`dt`） | 手动映射的用户态 DLL | 按需页解密缺页处理与页面描述符表 |
| `HtsyskNT.dll`（`sk`）/ `HtpecmNT.dll`（`pm`） | 第 1 代内核态 DLL | 内核手动映射器（`B21`）与进程监控模块（`BB0`） |
| `HtsysmNT` | 内核驱动（第 1 代） | 未鉴权的 Ring 0 Shellcode 执行 |
| `Htsysm7679` | 内核驱动（第 2 代，`0xAA01`） | 受边界限制（`offset < 0x1000`）的当前进程 `EPROCESS` 掩码双字改写 |
| `Htsysm767901` / `Htsysm1B4001` | 内核驱动（第 3 代，`0xAA02`） | 基于 `ObRegisterCallbacks` 并带路径/PID 豁免的句柄权限过滤 |
