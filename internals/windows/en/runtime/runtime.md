---
description: "What the Windows loader checks and changes at runtime before and after the original program starts."
---

# Runtime behavior

The runtime combines ordinary usermode loading work with environment checks, optional kernel support, and page-level code protection.

| Area | Detail |
|---|---|
| Startup | [Boot order, status values, and debug logging](startup-status.md) |
| Environment | [Usermode and kernel-assisted checks](environment-checks.md) |
| Code pages | [On-demand page changes and loader-code variation](page-protection.md) |
| Embedded components | [Manually mapped helper modules](mapped-modules.md) |
| Kernel | [Htsysm generations and responsibilities](kernel-components.md) |
