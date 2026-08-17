---
description: "Quick-reference tables of constants, offsets, and encodings used across the format, loader, and runtime."
---

# Appendix: constants and offsets

## Format magics

| Magic | Value | Meaning |
| --- | --- | --- |
| `KONN` | `0x4E4E4F4B` | Container stamp |

## Container constants

| Item | Value |
| --- | --- |
| Header region size / info-header offset | `4096` (`0x1000`) |
| Info header size | 32 bytes (8 dwords) |
| Minimum detection length | 4128 bytes |
| `decrypt_size` (payload chain length) | `info[6] - info[3] + 8192` |
| Section-data file base | `(~u32@0x1080) + 0x1000` |
| Companion pairing check | `stub[4096..4128] == companion[0..32]` |
| File-integrity dword | `u32@0x38 + 0x76543211` (stored obfuscated at offset `0x38`) |
| Config-cluster version stamp (32-bit) | `0x00007679` |
| Stage-5 markers (64-bit marker layout) | `70 6D 00 00 63 6D 00 00` and `00 00 00 40 01 00 00 00` |

## Primitive quick reference

| Primitive | Formula |
| --- | --- |
| Header KDF | `info[i+1] = k ^ cell; k = i² ^ (k + cell − i)` |
| Payload chain | `out = k ^ cell; k = i² ^ (k + cell + i)` |
| XOR-ROR dword cipher | `v = x ^ key; key += i; out = ror(v, shift) − i` (shift 19/21) |
| Byte rotate-3 | three `rol3`, XOR `b2`, `b` between; keys roll +1 per byte |
| Byte rotate-2 | three `rol2`, XOR `b2`, `b` between; keyed by address low byte |
| LFSR | seed 1, feedback `0x8003`, 8 bits/byte LSB-first; block length at `+95` |
| String cipher | `ror4(b) − key` (0 → `−key`), `key += 67` per byte |
| Page scramble (64-bit) | `mixed = ror15(key)+i; key = mixed+i; page[i*16 + (mixed&0xF)] ^= key`, block 0 advances only |
| Page scramble (32-bit) | same loop with `key = ror15(pk)` pre-step; `pk = page+1` or `0x8000*(page+1)` |
| CRC-32 | reflected, polynomial `0xEDB88320` |
| Checksum descriptor | `crc32(region) ^ length` |
| Triangular schedule | `key += 1..(m+1)*100` per round `m` |
| AES | CBC decryption; round count u16 at schedule+2; state big-endian; standard inverse T-tables |

## PE field offsets

| Field | PE32+ | PE32 |
| --- | --- | --- |
| `AddressOfEntryPoint` | `pe + 0x28` | `pe + 0x28` |
| Data-directory base | `pe + 0x88` (136) | `pe + 0x78` (120) |
| Import directory (DD[1]) | `pe + 0x90` | `pe + 0x80` |
| Base relocation (DD[5]) | `pe + 0xB0` | `pe + 0xA0` |
| TLS (DD[9]) | `pe + 0xD0` | `pe + 0xC0` |
| IAT (DD[12]) | `pe + 0xE8` | `pe + 0xD8` |
| CLR/COM descriptor (DD[14]) | `pe + 0xF8` | `pe + 0xE0` |
| `DllCharacteristics` | `pe + 0x5E` | `pe + 0x5E` |
| `SizeOfImage` | `pe + 0x50` | `pe + 0x50` |
| `IMAGE_FILE_DLL` bit | `0x2000` in Characteristics (`pe + 0x16`) | same |

## Bytecode stub opcode map

| Bytes | Instruction | Operation |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | add |
| `2C ib` | `SUB AL, imm8` | sub |
| `34 ib` | `XOR AL, imm8` | xor |
| `90` | `NOP` | none |
| `C0 /0 ib` | `ROL AL, imm8` | rol |
| `C0 /1 ib` | `ROR AL, imm8` | ror |
| `FE /0` | `INC AL` | inc |
| `FE /1` | `DEC AL` | dec |
| `C3` | `RET` | end |

ModR/M must be register-direct `AL` (`mod=3, rm=0`); anything else is invalid.

## Cross-references

- Status codes and the boot sequence: [Runtime behavior](../runtime/startup-status.md#the-boot-sequence-and-status-codes)
- Module codes and driver generations: [Kernel drivers and submodules](../runtime/kernel-components.md)
- il2cpp metadata constants: [il2cpp metadata obfuscation](il2cpp-metadata.md)
- Huffman table/token format: [Data transformation primitives](../data-transforms/compression.md#the-huffmanlz-compression-format)

## Verification suite

Every Python snippet in this document was verified before publication: each function's output was compared byte-for-byte against an independent reference port of the algorithms on identical inputs (30 test vectors, all matching). The complete, runnable snippet files and the comparison harness are published in the [Verification & reference](https://app.gitbook.com/s/8S0xnfw9UP9A2yylicaA/) section of this site — `python run_tests.py` re-runs the full comparison.
