---
description: "The arithmetic, module, container, and compression layers used by Android streams."
---

# Data transforms

The Android format combines a small arithmetic transform for the outer header with module-specific transforms for container records. Compression is a separate layer and is validated by both its input consumption and its output length.

The pages here describe observable fields and equations. They avoid assigning new names to intermediate states that are not present in the format.
