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

The sparse page transform needs a separate decision. A recognizable CRT entry stub (`48 83 EC ib / E8 / 48 83 C4 ib / E9`, matching stack immediates) is strong evidence when it is the only candidate — including “no transform” — whose decoded `call` and `jmp` targets both remain inside `.text`. Otherwise, compare how much each candidate restores expected `0xCC` padding across several pages and require both a margin over the unchanged baseline and an absolute floor. Small gains are the noise of XORing 255 positions per page and must not trigger a transform. 32-bit images use the same padding test to choose `page+1` versus `0x8000*(page+1)`, or to skip the pass on already-plaintext `.text`.

If no candidate passes its content check, stop at that stage. Returning a plausible but silently damaged PE makes later observations unreliable.

