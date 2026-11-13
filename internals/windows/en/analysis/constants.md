---
description: "Reference tables of magics, container formulas, cipher equations, PE32/PE32+ offsets, and bytecode opcodes."
icon: sliders
---

# Constants and offsets

## Container constants and magics

| Item | Value |
| --- | --- |
| Format magic (`info[1]`) | `0x4E4E4F4B` (`KONN` in little-endian ASCII) |
| Outer PE header region / `info` offset | `4096` (`0x1000`) |
| Encrypted `info` header length | `32` bytes (`8` dwords) |
| Minimum candidate file length | `4128` (`0x1020`) bytes |
| `decrypt_size` (standard / full-payload PE32) | `info[6] - info[3] + 8192` / `info[5]` (compact PE32 fallback) |
| Section-data file base | `(~u32@0x1080 + 0x1000) & 0xFFFFFFFF` |
| Companion (`._`) pairing check | `stub[4096..4128] == companion[0..32]` |
| Companion entry-thunk markers (`+53` / `+58`) | `~0x1000` / `~u32("._\0\0")` (`~0` on single-file PE32+) |
| Dword written at `image[info[3]]` after payload copy | `4096` (`0x1000`) |
| PE32 `EighthStage` cluster stamp | `0x00007679` (when present) |
| 64-bit Stage 5 markers (classic layout) | `70 6D 00 00 63 6D 00 00` (`"pm\0\0cm\0\0"`) and `00 00 00 40 01 00 00 00` |

## Cipher and checksum quick reference

| Primitive | Formula (unsigned 8/32-bit wraparound) |
| --- | --- |
| `header_kdf` | `info[i + 1] = k ^ cell; k = (i * i) ^ ((k + cell - i) & MASK32)` |
| `payload_xor_chain` | `k0 = info[0] + ~decrypt_size; out = k ^ cell; k = (i * i) ^ ((k + cell + i) & MASK32)` |
| `xor_ror_dwords` (`dd3`) | `v = x ^ key; key += i; out = ror32(v, shift) - i` (64-bit: `19`/`21`; 32-bit: 8-shift set) |
| `byte_rotate3` (`dd4`) | `b = ((addr >> 8) + addr) & 0xFF; b2 = b + 1`; `rol8` by 3 three times, XOR `b2` then `b` |
| `byte_rotate2` (`dd5`) | `b = va & 0xFF; b2 = b + 1`; `rol8` by 2 three times, XOR `b2` then `b` (position-local) |
| `lfsr_keystream` (`dd6`) | Seed `1`, polynomial `0x8003`, 8 bits/byte LSB-first; plaintext length at `pos + 95` |
| `string_cipher` (`dd7`) | `ror8(b, 4) - key` (`0 -> -key`), `key += 67`; keyed by `name_rva & 0xFF` or `hint_name_rva & 0xFF` |
| `page_scramble` (`dd8`, 64-bit) | `mixed = ror32(key, 15) + i; key = mixed + i`; XOR `page[i * 16 + (mixed & 0xF)] ^= key & 0xFF` for `i >= 1` |
| `page_scramble_pe32` (`dd8`, 32-bit) | Pre-step `key = ror32(pk, 15)` (`pk = page + 1` or `0x8000 * (page + 1)`), then `i = 1..255` |
| `crc32` & `calculate_checksum` | Reflected CRC-32 (`0xEDB88320`); region checksum `crc32(region) ^ length` |
| `advance_key` | Add `1 .. ((m + 1) * 100)` for `m in 0..iterations` |
| `aes_decrypt` | Zero-IV AES-CBC; `u16` round count at `key_offset + 2`; big-endian state words; standard GF(2⁸) inverse T-tables |

## PE header offsets (`pe = u32@0x3C`)

| Field | PE32+ (`0x20B`) | PE32 (`0x10B`) |
| --- | --- | --- |
| `Characteristics` (`IMAGE_FILE_DLL = 0x2000`) | `pe + 0x16` | `pe + 0x16` |
| `OptionalHeader.Magic` | `pe + 0x18` | `pe + 0x18` |
| `AddressOfEntryPoint` | `pe + 0x28` | `pe + 0x28` |
| `SizeOfImage` | `pe + 0x50` | `pe + 0x50` |
| `DllCharacteristics` | `pe + 0x5E` | `pe + 0x5E` |
| Data-directory array start | `pe + 0x88` (`136`) | `pe + 0x78` (`120`) |
| Export directory (`DD[0]`) | `pe + 0x88` | `pe + 0x78` |
| Import directory (`DD[1]`) | `pe + 0x90` | `pe + 0x80` |
| Resource directory (`DD[2]`) | `pe + 0x98` | `pe + 0x88` |
| Base relocation (`DD[5]`) | `pe + 0xB0` | `pe + 0xA0` |
| TLS directory (`DD[9]`) | `pe + 0xD0` | `pe + 0xC0` |
| IAT (`DD[12]`) | `pe + 0xE8` | `pe + 0xD8` |
| CLR / COM descriptor (`DD[14]`) | `pe + 0xF8` | `pe + 0xE8` |

## Per-build `AL` bytecode opcodes

| Bytes | Instruction | Decoded operation |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | skipped |
| `C0 C0 ib` | `ROL AL, imm8` | `("rol", imm)` |
| `C0 C8 ib` | `ROR AL, imm8` | `("ror", imm)` |
| `FE C0` | `INC AL` | `("inc",)` |
| `FE C8` | `DEC AL` | `("dec",)` |
| `C3` | `RET` | end of stub |

## Verification suite

Every transform above is checked against an independent Rust port across 31 comparisons over 25 named reference records in [Verification & reference](https://app.gitbook.com/s/8S0xnfw9UP9A2yylicaA/). Run `python verification/run_tests.py` and `python verification/verify_docs.py` from the repository root to re-verify all implementations and documentation blocks.
