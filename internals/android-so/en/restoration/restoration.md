---
description: "Reassemble image bytes, dynamic-linking data, and the final ELF layout."
---

# Restoration

Restoration is staged. First, records are dispatched to the modules that can decode them. Next, dynamic-linking tables and hidden symbols are materialized. Finally, the recovered ranges are written into a coherent ELF image and validated again.

The output is considered usable only after both byte ranges and ELF relationships agree.
