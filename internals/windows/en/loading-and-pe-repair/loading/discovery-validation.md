---
description: "Why loader structures are discovered by shape and how false candidates are rejected."
---

# Structural discovery and validation

## Why everything is scanned, and how wrong answers are avoided

A recurring design fact is that few container objects remain at one offset across builds. Table placement changes, PE32 layouts apply `ss_shift`, newer builds omit markers, and unrelated bytes can resemble pointers or transform programs. The loader knows the layout compiled into its own build; a static analysis has to recover that layout from the file.

Do not accept the first match. Use several independent checks:

- Check table shapes such as an anchor dword equal to `info[3]`, the `(1, 0, info[3], 0)` entry, and bounded `(offset, size)` pairs.
- Parse a candidate transform program to its actual `RET`; reject invalid opcodes, invalid ModR/M fields, and streams that only contain a coincidental `0xC3` operand byte.
- Require pointers to identify ranges inside the current image or protected file. Do not use pointer plausibility as the only check.
- Trial-decrypt candidate descriptors without committing the change, then require source and destination ranges to fit.
- Replay the first compressed section record and require decompression to finish at the declared output size. A candidate that only works for raw-copy records has not yet been validated.
- Verify the checksum chain where the layout supplies it.

The sparse page transform needs a separate decision. A recognizable entry stub is strong evidence when its decoded call and jump targets both remain inside `.text`. Otherwise, compare how much each candidate restores expected `0xCC` padding across several pages and require a meaningful improvement over the unchanged bytes. Small gains are normal random noise and must not trigger a transform.

If no candidate passes its content check, stop at that stage. Returning a plausible but silently damaged PE makes later observations unreliable.

