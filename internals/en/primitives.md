---
description: "The ciphers, compression format, per-build bytecode permutation, and checksum chaining CrackProof applies to protected content."
---

# Data transformation primitives

Every layer of the container is built from a small set of primitives. Once each one is defined, the staged loader is "apply primitive N at offset X with key Y" repeated in a strict order. This page defines each primitive precisely, with a Python implementation.

{% hint style="success" %}
Every code snippet on this page has been executed and verified against the algorithms as implemented in protected binaries: each function's output was compared byte-for-byte with a reference port on identical inputs.
{% endhint %}

## Conventions

All buffers are mutable byte arrays (`bytearray`); the original algorithms work in place. Helpers used throughout:

```python
MASK32 = 0xFFFFFFFF

def get_u16(d, off):
    return d[off] | (d[off + 1] << 8)

def get_u32(d, off):
    return d[off] | (d[off + 1] << 8) | (d[off + 2] << 16) | (d[off + 3] << 24)

def put_u32(d, off, value):
    d[off:off + 4] = (value & MASK32).to_bytes(4, "little")

def rol32(x, n): return ((x << n) | (x >> (32 - n))) & MASK32
def ror32(x, n): return ((x >> n) | (x << (32 - n))) & MASK32
def rol8(x, n):  return ((x << n) | (x >> (8 - n))) & 0xFF
def ror8(x, n):  return ((x >> n) | (x << (8 - n))) & 0xFF
```

## The rolling-key family

Two ciphers share one rolling-key design: the key starts from a seed, each cell is XORed with the current key, and the key then rolls forward by mixing in the cell value, the loop index, and the square of the index. The header KDF (see [The protected file format](file-format.md)) is the 8-cell instance; the payload body cipher is the long-form instance with a different seed and update rule:

```python
def payload_xor_chain(file_data, out, info, decrypt_size):
    """Decrypt the bulk of the payload into the image buffer."""
    base_src = (info[4] + 4096) & MASK32
    k = (info[0] + (~decrypt_size & MASK32)) & MASK32
    for i in range(decrypt_size >> 2):
        cell = get_u32(file_data, (base_src + 4 * i) & MASK32)
        put_u32(out, (info[3] + 4 * i) & MASK32, k ^ cell)
        k = (i * i) ^ ((k + cell + i) & MASK32)
```

Because the key rolls forward with each dword, the chain must be decrypted from the start — random access into the payload is impossible without replaying the chain.

## XOR + rotate-right dword cipher

This cipher unwraps each stage's pointer blocks. It reads a `(base_addr, length)` descriptor from the buffer itself, then transforms each dword: XOR with the rolling key, rotate right by a fixed shift, and subtract the loop index. The shift is 19 or 21 depending on the call site.

```python
def xor_ror_dwords(d, pos, key, shift):
    base_addr = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    for i in range(length >> 2):
        off = (base_addr + 4 * i) & MASK32
        v = get_u32(d, off) ^ key
        key = (key + i) & MASK32
        put_u32(d, off, (ror32(v, shift) - i) & MASK32)
```

32-bit builds additionally brute-force the shift for one stage from the candidate set `[19, 21, 17, 23, 15, 25, 13, 11]`, accepting the shift whose output parses as a valid stage table (see [The staged loader](staged-loader.md)).

## Triple byte-rotation ciphers

Two byte ciphers share a structure: three bit-rotations per byte, with two rolling key bytes XORed between rotations. They differ in rotation amount and in how the initial key is derived.

```python
def byte_rotate3(d, pos):
    """Descriptor-addressed variant: rotate by 3, keyed from the address."""
    base_addr = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    b = ((base_addr >> 8) + base_addr) & 0xFF
    b2 = (b + 1) & 0xFF
    for i in range(length):
        idx = base_addr + i
        x = rol8(d[idx], 3) ^ b2
        x = rol8(x, 3) ^ b
        d[idx] = rol8(x, 3)
        b = (b + 1) & 0xFF
        b2 = (b2 + 1) & 0xFF

def byte_rotate2(d, va, size):
    """Position-keyed variant: rotate by 2, keyed from the address itself."""
    b = va & 0xFF
    b2 = (b + 1) & 0xFF
    for i in range(size):
        idx = va + i
        x = rol8(d[idx], 2) ^ b2
        x = rol8(x, 2) ^ b
        d[idx] = rol8(x, 2)
        b = (b + 1) & 0xFF
        b2 = (b2 + 1) & 0xFF
```

The position-keyed variant has a property the loader's table walks rely on heavily: **each output byte depends only on the input byte and the low 8 bits of its address** — there is no cross-byte state. Any four bytes can therefore be trial-decrypted without touching the rest of the buffer:

```python
def trial_byte_rotate2(d, va):
    """Non-mutating 4-byte trial decrypt."""
    out = bytearray(4)
    for i in range(4):
        b = (va + i) & 0xFF
        x = rol8(d[va + i], 2) ^ ((b + 1) & 0xFF)
        x = rol8(x, 2) ^ b
        out[i] = rol8(x, 2)
    return get_u32(out, 0)
```

16-byte descriptors throughout the loader are encrypted with `byte_rotate2`, chained positionally: each descriptor's key comes from its own address, and the walk terminates on a zero length field.

## The LFSR keystream

The per-build bytecode stubs (see below) are themselves wrapped in an LFSR keystream. The stream is data-independent — seed 1, feedback polynomial `0x8003`, eight bits emitted per byte, LSB first — so it can be replayed at any position, which is what makes trial-decoding candidate stub locations cheap:

```python
def lfsr_keystream(n):
    out = bytearray(n)
    state = 1
    for i in range(n):
        b = 0
        for k in range(8):
            b |= (state & 1) << k
            state = (state << 1) & MASK32
            if state & 0x8000:
                state ^= 0x8003
        out[i] = b
    return out

def lfsr_decrypt_block(d, pos):
    """XOR a bytecode stub with the keystream. The block length is stored
    unencrypted at pos+95."""
    length = d[pos + 95]
    ks = lfsr_keystream(length)
    for i in range(length):
        d[pos + i] ^= ks[i]
```

A stub block occupies a fixed 96-byte slot; the byte at `pos + 95` is the (unencrypted) length of the program inside.

## The import-name string cipher

DLL names and imported function names are encrypted with a rolling byte cipher: nibble swap, subtract the key, step the key by 67. The initial key is the low byte of the string's RVA — so a name cannot be decrypted without knowing where it lives.

```python
def string_cipher(d, pos, key):
    """Decrypt a NUL-terminated string in place."""
    i = 0
    while d[pos + i] != 0:
        b = ror8(d[pos + i], 4)
        b = (b - key) & 0xFF
        if b == 0:
            b = (-key) & 0xFF
        d[pos + i] = b
        key = (key + 67) & 0xFF
        i += 1
```

The `b == 0` remap avoids producing a NUL mid-string (which would truncate the walk): if the subtraction lands on zero, the byte is replaced by the two's complement of the key instead.

## The per-page code scramble

Executable sections carry a sparse, page-granular scramble on top of everything else: one byte per 16-byte block is XORed, at an in-block offset that varies per block. The pattern skips block 0 (its key state still advances). 255 of each page's 4096 bytes are touched.

```python
def page_scramble(d, va, size, key):
    """64-bit form. `key` is the absolute page index shifted left by a
    build-specific amount (0 or 15)."""
    for i in range(size >> 4):
        mixed = (ror32(key, 15) + i) & MASK32
        key = (mixed + i) & MASK32
        if i == 0:
            continue
        d[va + i * 16 + (mixed & 0xF)] ^= key & 0xFF

def page_scramble_pe32(d, pa, page, big_formula):
    """32-bit form. The page key is (page+1) or 0x8000*(page+1)."""
    key = (0x8000 * (page + 1)) & MASK32 if big_formula else page + 1
    key = ror32(key, 15)
    for bi in range(1, 256):
        rk = ror32(key, 15)
        ri = (rk + bi) & MASK32
        key = (ri + bi) & MASK32
        d[pa + bi * 16 + (ri & 0xF)] ^= key & 0xFF
```

{% hint style="warning" %}
The shift (64-bit: 0 or 15) and the formula choice (32-bit: `page+1` or `0x8000*(page+1)`) are **not recorded anywhere in the file**. Two builds can carry byte-identical configuration stamps yet require different choices. The only reliable discriminator is the code content itself: replay the scramble on sample pages under each candidate and count how many positions decode to `0xCC` (the MSVC `int3` padding byte). The correct choice restores padding disproportionately; a wrong one scrambles roughly one byte per 16. Some modules (native DLLs) have plaintext code and must not be descrambled at all.
{% endhint %}

## CRC-32 checksums

Checksums use the standard reflected CRC-32 (polynomial `0xEDB88320`, the zlib/Ethernet CRC — `crc32(b"123456789") == 0xCBF43926`). Two descriptor forms appear:

```python
def _build_crc_table():
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = 0xEDB88320 ^ (c >> 1) if c & 1 else c >> 1
        table.append(c)
    return table

CRC_TABLE = _build_crc_table()

def crc32_append(initial, data):
    crc = ~initial & MASK32
    for b in data:
        crc = CRC_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return ~crc & MASK32

def crc32(data):
    return crc32_append(0, data)

def calculate_checksum(d, pos):
    """crc32(region) ^ length, where (offset, length) is read from d[pos]."""
    offset = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    return crc32(d[offset:offset + length]) ^ length
```

A second form chains over the **original file bytes** with a running initial value (`crc32_append` with the previous result as `initial`), used by the validation-only walk described in [The staged loader](staged-loader.md).

## The triangular key schedule

Several stage keys are "advanced" by adding structured integer series — each iteration adds every integer from 1 to `(m+1) * 100`:

```python
def advance_key(key, iterations):
    for m in range(iterations):
        bound = ((m + 1) * 25) << 2
        for n in range(1, bound + 1):
            key = (key + n) & MASK32
    return key
```

The seed is content read from the previously decrypted stage, so the advanced key only comes out right when everything before it decrypted correctly — one half of the tamper-evidence design (the other half is the checksum chain at the end of this page).

## The block cipher: AES-CBC with an in-buffer key schedule

Bulk content — stages and section blocks — is protected with AES decryption in CBC mode. Two design choices are worth noting:

- **The key schedule lives inside the data buffer itself.** A small header at `key_offset` holds the round count (little-endian u16 at `key_offset + 2`), followed by `(rounds + 1)` 16-byte round keys. No separate key material needs extracting; the schedule is unpacked along with everything else.
- **The tables are the standard AES decryption T-tables** (InvSubBytes fused with InvMixColumns), generated below from GF(2⁸) arithmetic — public AES constants, not proprietary data. State words are loaded and stored big-endian.

```python
def _gf_mul(a, b):
    """Multiply in GF(2^8) with the AES reduction polynomial."""
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return p

def _inverse_sbox():
    inv = [0] * 256
    for a in range(1, 256):
        for b in range(1, 256):
            if _gf_mul(a, b) == 1:
                inv[a] = b
                break
    fwd = [0] * 256
    for i in range(256):
        x = s = inv[i]
        for _ in range(4):
            s = ((s << 1) | (s >> 7)) & 0xFF
            x ^= s
        fwd[i] = x ^ 0x63
    isb = [0] * 256
    for i in range(256):
        isb[fwd[i]] = i
    return isb

def _build_tables():
    """Each table has 256 u32 entries. SBOX broadcasts invsbox(x) to all four
    lanes; COLUMMIX1 holds [0x0b*s, 0x0d*s, 0x09*s, 0x0e*s] and COLUMMIX2/3/4
    are its one-, two- and three-byte rotations."""
    isb = _inverse_sbox()
    sbox = bytearray(1024)
    cm = [bytearray(1024) for _ in range(4)]
    for x in range(256):
        s = isb[x]
        lanes = [_gf_mul(0x0B, s), _gf_mul(0x0D, s), _gf_mul(0x09, s), _gf_mul(0x0E, s)]
        for j in range(4):
            sbox[x * 4 + j] = s
            for t in range(4):
                cm[t][x * 4 + j] = lanes[(j + t) % 4]
    return sbox, cm

_SBOX, _CM = _build_tables()

def _aes_round(d, pos, key_offset, rounds):
    """Decrypt one 16-byte block in place. The state words are loaded and
    stored big-endian; the round keys are read from the same buffer."""
    n = [int.from_bytes(d[pos + 4 * i:pos + 4 * i + 4], "big")
         ^ get_u32(d, key_offset + 4 * i) for i in range(4)]

    # Middle rounds: InvSubBytes + InvShiftRows + InvMixColumns, fused into
    # four T-table lookups per state word, plus the round key.
    for r in range(1, rounds):
        off = key_offset + r * 16
        n = [
            get_u32(_CM[1], ((n[3] >> 16) & 0xFF) * 4) ^ get_u32(_CM[2], ((n[2] >> 8) & 0xFF) * 4)
            ^ get_u32(_CM[0], (n[0] >> 24) * 4) ^ get_u32(_CM[3], (n[1] & 0xFF) * 4) ^ get_u32(d, off),
            get_u32(_CM[1], ((n[0] >> 16) & 0xFF) * 4) ^ get_u32(_CM[0], (n[1] >> 24) * 4)
            ^ get_u32(_CM[2], ((n[3] >> 8) & 0xFF) * 4) ^ get_u32(_CM[3], (n[2] & 0xFF) * 4) ^ get_u32(d, off + 4),
            get_u32(_CM[1], ((n[1] >> 16) & 0xFF) * 4) ^ get_u32(_CM[2], ((n[0] >> 8) & 0xFF) * 4)
            ^ get_u32(_CM[0], (n[2] >> 24) * 4) ^ get_u32(_CM[3], (n[3] & 0xFF) * 4) ^ get_u32(d, off + 8),
            get_u32(_CM[2], ((n[1] >> 8) & 0xFF) * 4) ^ get_u32(_CM[1], ((n[2] >> 16) & 0xFF) * 4)
            ^ get_u32(_CM[0], (n[3] >> 24) * 4) ^ get_u32(_CM[3], (n[0] & 0xFF) * 4) ^ get_u32(d, off + 12),
        ]

    # Final round: S-box substitution with the ShiftRows lane permutation.
    s = [
        (get_u32(_SBOX, (n[0] >> 24) * 4) & 0xFF000000) | (get_u32(_SBOX, ((n[3] >> 16) & 0xFF) * 4) & 0x00FF0000)
        | (get_u32(_SBOX, ((n[2] >> 8) & 0xFF) * 4) & 0x0000FF00) | (get_u32(_SBOX, (n[1] & 0xFF) * 4) & 0x000000FF),
        (get_u32(_SBOX, (n[1] >> 24) * 4) & 0xFF000000) | (get_u32(_SBOX, ((n[0] >> 16) & 0xFF) * 4) & 0x00FF0000)
        | (get_u32(_SBOX, ((n[3] >> 8) & 0xFF) * 4) & 0x0000FF00) | (get_u32(_SBOX, (n[2] & 0xFF) * 4) & 0x000000FF),
        (get_u32(_SBOX, (n[2] >> 24) * 4) & 0xFF000000) | (get_u32(_SBOX, ((n[1] >> 16) & 0xFF) * 4) & 0x00FF0000)
        | (get_u32(_SBOX, ((n[0] >> 8) & 0xFF) * 4) & 0x0000FF00) | (get_u32(_SBOX, (n[3] & 0xFF) * 4) & 0x000000FF),
        (get_u32(_SBOX, (n[3] >> 24) * 4) & 0xFF000000) | (get_u32(_SBOX, ((n[2] >> 16) & 0xFF) * 4) & 0x00FF0000)
        | (get_u32(_SBOX, ((n[1] >> 8) & 0xFF) * 4) & 0x0000FF00) | (get_u32(_SBOX, (n[0] & 0xFF) * 4) & 0x000000FF),
    ]

    last = key_offset + rounds * 16
    for i in range(4):
        d[pos + 4 * i:pos + 4 * i + 4] = (s[i] ^ get_u32(d, last + 4 * i)).to_bytes(4, "big")

def aes_decrypt(d, pos, size, key_offset):
    """CBC decryption over `size` bytes at `pos`; the schedule lives in the
    same buffer at `key_offset` (round count at key_offset+2)."""
    rounds = get_u16(d, key_offset + 2)
    prev = bytes(16)
    for i in range(size >> 4):
        p = pos + i * 16
        cur = bytes(d[p:p + 16])
        _aes_round(d, p, key_offset + 4, rounds)
        for j in range(16):
            d[p + j] ^= prev[j]
        prev = cur
```

Each block is decrypted with `_aes_round` (initial key XOR, `rounds − 1` T-table rounds, and a final SubBytes/ShiftRows-only round — the canonical AES inverse structure) and then XORed with the previous ciphertext block (zero IV).

## The Huffman/LZ compression format

Most payload blocks are compressed with a custom hybrid: a Huffman-coded token stream where tokens are literals, run fills, or LZ back-references. The decoding table travels with the data, at `key_offset` in the same buffer.

**Table format.** The table is a forest of 3-byte entries: a u16 symbol/child field and a u8 code-length field. Root selection reads 8 bits of input as the entry index. The top bit (`0x8000`) marks a leaf; internal nodes store the index of the first of a sibling pair, and one more input bit chooses between them. The stored length byte counts the bits consumed so far (8 for a root), so a leaf reached after N internal levels has a total code length of 8 + N bits.

**Token format.** A token's bits 8–9 select the mode, bits 0–7 are the payload:

| Mode | Meaning |
| --- | --- |
| `0x000` | Literal: emit the payload byte |
| `0x100` | Count accumulator: append the payload to a big-endian pending value (emits nothing by itself) |
| `0x200` | Run fill: repeat the previously written 1/2/4-byte unit `pending × payload` times |
| `0x300` | LZ back-reference: copy `payload` bytes from `pending + payload` bytes behind the output cursor |

```python
def decompress(d, src, dest, key_offset, s_size, d_size):
    """Decompress s_size bytes at `src` into d_size bytes at `dest`,
    in place within buffer `d`. Returns True when exactly d_size bytes
    were produced."""
    bit_pos = 0
    buf = bytearray(d[src:src + s_size]) + bytearray(3)  # 3 bytes of slack
    buf_off = 0
    src_consumed = 0
    pending = 0
    written = 0

    while src_consumed < s_size and written < d_size:
        word = get_u32(buf, buf_off) >> bit_pos
        tab_addr = key_offset + (word & 0xFF) * 3
        tab = get_u16(d, tab_addr)
        if tab & 0x8000:  # leaf
            tab &= 0x7FFF
            bits = d[tab_addr + 2]
        else:             # internal node: walk down one bit per level
            bits = d[tab_addr + 2]
            if bits >= 32:
                return False
            mask = 1 << bits
            bits += 1
            idx = (tab & 0x7FFF) + (1 if word & mask else 0)
            t2 = get_u16(d, key_offset + idx * 3)
            depth = 0
            while not (t2 & 0x8000):
                depth += 1
                if depth > 64:
                    return False
                mask <<= 1
                bits += 1
                idx = (t2 & 0x7FFF) + (1 if word & mask else 0)
                t2 = get_u16(d, key_offset + idx * 3)
            tab = t2 & 0x7FFF

        bit_pos += bits
        advance = bit_pos // 8
        buf_off += advance
        src_consumed += advance
        bit_pos %= 8

        mode = tab & 0x300
        payload = tab & 0xFF
        if mode == 0x000:  # literal
            step = 1
            d[dest] = payload
        elif mode == 0x100:  # count accumulator
            step = 0
            if pending >= 256:
                return False
            pending = payload if pending == 0 else (pending << 8) | payload
        elif mode == 0x200:  # run fill
            if pending == 0:
                pending = 1
            step = pending * payload
            if step + written > d_size:
                return False
            if payload == 1:
                if dest < 1:
                    return False
                v = d[dest - 1]
                for k in range(pending):
                    d[dest + k] = v
            elif payload == 2:
                if dest < 2:
                    return False
                v = get_u16(d, dest - 2)
                for k in range(pending):
                    put_u16(d, dest + k * 2, v)
            elif payload == 4:
                if dest < 4:
                    return False
                v = get_u32(d, dest - 4)
                for k in range(pending):
                    put_u32(d, dest + k * 4, v)
            else:
                return False
            pending = 0
        else:  # 0x300: LZ back-reference
            step = payload
            if written + payload > d_size or pending + payload > written:
                return False
            back = pending + payload
            for k in range(payload):
                d[dest + k] = d[dest + k - back]
            pending = 0

        dest += step
        written += step
        if bits == 0 and step == 0:
            return False

    return written == d_size
```

The boolean result is a corruption signal — and, importantly, an **oracle**: where the container does not record a key or shift choice, candidates are tried until one decompresses cleanly. Several such trial-and-validate points appear in [The staged loader](staged-loader.md).

## The per-build bytecode permutation

The most distinctive layer: CrackProof does not hardcode a fixed per-byte transform for payload data. At pack time it **generates a unique x86 stub for each build** — a function that takes one byte in `AL`, applies a short random sequence of arithmetic/rotate instructions, and returns. The loader runs this stub over every payload byte between the block-cipher pass and decompression. Two protected files from different builds therefore share no payload permutation.

The stub is stored wrapped in the LFSR keystream (above). Rather than executing x86, the instruction bytes can be decoded into a tiny op list and interpreted — only a narrow instruction subset ever appears:

| Bytes | x86 instruction | VM operation |
| --- | --- | --- |
| `04 ib` | `ADD AL, imm8` | `("add", imm)` |
| `2C ib` | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib` | `XOR AL, imm8` | `("xor", imm)` |
| `90` | `NOP` | skipped |
| `C0 /0 ib` | `ROL AL, imm8` | `("rol", imm)` |
| `C0 /1 ib` | `ROR AL, imm8` | `("ror", imm)` |
| `FE /0` | `INC AL` | `("inc",)` |
| `FE /1` | `DEC AL` | `("dec",)` |
| `C3` | `RET` | end of program |

For `C0`/`FE` the ModR/M byte must encode register-direct `AL` (`mod=3, rm=0`); the reg field selects the sub-operation. Anything else fails the parse — and that strictness is what makes trial-decoding candidate stub locations reliable: decrypted garbage essentially never parses as a valid program ending in `RET`.

```python
def generate(data, offset=0):
    """Decode the stub at `offset` into an op list, or return None if the
    byte stream is not a valid stub (must terminate in RET)."""
    pos = offset
    ops = []

    def take():
        nonlocal pos
        if pos >= len(data):
            return None
        b = data[pos]
        pos += 1
        return b

    while True:
        op = take()
        if op is None:
            return None
        if op == 0x04:
            imm = take()
            if imm is None:
                return None
            ops.append(("add", imm))
        elif op == 0x2C:
            imm = take()
            if imm is None:
                return None
            ops.append(("sub", imm))
        elif op == 0x34:
            imm = take()
            if imm is None:
                return None
            ops.append(("xor", imm))
        elif op == 0x90:
            pass
        elif op in (0xC0, 0xFE):
            modrm = take()
            if modrm is None:
                return None
            mod, reg, rm = modrm >> 6, (modrm >> 3) & 7, modrm & 7
            if mod != 3 or rm != 0 or reg > 1:
                return None
            if op == 0xC0:
                imm = take()
                if imm is None:
                    return None
                ops.append(("rol" if reg == 0 else "ror", imm))
            else:
                ops.append(("inc" if reg == 0 else "dec",))
        elif op == 0xC3:
            return ops
        else:
            return None

def apply_ops(ops, x):
    """Run an op chain over a single byte."""
    for op in ops:
        name = op[0]
        if name == "add":
            x = (x + op[1]) & 0xFF
        elif name == "sub":
            x = (x - op[1]) & 0xFF
        elif name == "xor":
            x ^= op[1]
        elif name == "rol":
            n = op[1] & 7
            x = ((x << n) | (x >> (8 - n))) & 0xFF
        elif name == "ror":
            n = op[1] & 7
            x = ((x >> n) | (x << (8 - n))) & 0xFF
        elif name == "inc":
            x = (x + 1) & 0xFF
        elif name == "dec":
            x = (x - 1) & 0xFF
    return x
```

Two structural properties follow directly:

- **The chain is a permutation of the 256 byte values.** Every op is reversible (`add↔sub`, `xor` self-inverse, `rol↔ror`, `inc↔dec`), so the whole map is a bijection. It can be precomputed as a 256-entry translation table (`bytes(apply_ops(ops, i) for i in range(256))`), and an inverse chain exists by walking the op list backwards with each op swapped for its inverse.
- **Finding the stub is a search problem, not a fixed offset.** Because the keystream is data-independent, candidate positions are trial-XORed and parsed; the lowest position that decodes to a valid program (enough real operations, terminating in `RET`) is the real stub. Later valid parses are coincidental decodes of trailing filler.

One build carries **two** such stubs: one used while decrypting the final loader stage, and a second, independent one applied to every section data block.

## The checksum chain

The last primitive is not a cipher but the way keys are composed. A stage's decryption key is typically:

```
stage_key = xor_accumulator ^ crc32_checksum_of_earlier_content ^ content_derived_seed
```

- The **xor accumulator** is built by walking a table of `(offset, length)` region descriptors and XORing their `calculate_checksum` values.
- The **checksums** are CRC-32 over bytes that only exist in plaintext after the preceding stages decrypted correctly.
- The **seed** is a dword read from freshly decrypted content, usually advanced with `advance_key`.

The consequence: stages cannot be decrypted out of order, and any byte modified anywhere upstream corrupts every key derived from it downstream. The chain is the container's tamper-evidence mechanism — and, inverted, it is also what makes an unpacked image verifiable: a single wrong choice anywhere leaves later stages undecryptable rather than subtly wrong. How each build family composes these ingredients is the subject of the next page.
