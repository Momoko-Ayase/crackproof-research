---
description: "Windows 加载器在原程序启动前后执行的检查与运行时修改。"
---

# 运行时行为

运行时同时执行常规用户态加载工作、环境检查、可选内核支持与页级代码保护。

| 范围 | 详细内容 |
|---|---|
| 启动 | [启动顺序、状态值与调试日志](startup-status.md) |
| 环境 | [用户态与内核辅助检查](environment-checks.md) |
| 代码页 | [按需页变化与加载器代码差异](page-protection.md) |
| 嵌入组件 | [手动映射辅助模块](mapped-modules.md) |
| 内核 | [Htsysm 代际与职责](kernel-components.md) |
