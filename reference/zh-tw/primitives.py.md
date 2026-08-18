---
description: "滾動密鑰、旋轉、LFSR、字符串、頁置亂、按需頁、CRC-32、校驗和與三角調度。"
---

# primitives.py

除分組密碼、解壓器與字節碼 VM 之外的全部數據變換——[數據變換](https://app.gitbook.com/s/sFi4W2Zr1UBoxZd5YI3A/shu-ju-bian-huan/data-transforms)中記載的各密碼與校驗和。

```python
"""Reference implementations of the protection scheme's data transforms.

Written for readability: every function mirrors the algorithm the loader
executes at runtime, using plain Python with explicit 32-bit/8-bit wrapping
(Python ints don't overflow, so masks are applied where the original uses
fixed-width machine words).

Conventions:
  - All buffers are bytearrays (mutable, like the loader's in-place passes).
  - get_u32 / put_u32 are little-endian, matching the x86 environment.
"""

# ---------------------------------------------------------------------------
# Fixed-width helpers
# ---------------------------------------------------------------------------

MASK32 = 0xFFFFFFFF


def get_u16(d, off):
    return d[off] | (d[off + 1] << 8)


def get_u32(d, off):
    return d[off] | (d[off + 1] << 8) | (d[off + 2] << 16) | (d[off + 3] << 24)


def put_u32(d, off, value):
    value &= MASK32
    d[off:off + 4] = value.to_bytes(4, "little")


def rol32(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK32


def ror32(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK32


def rol8(x, n):
    return ((x << n) | (x >> (8 - n))) & 0xFF


def ror8(x, n):
    return ((x >> n) | (x << (8 - n))) & 0xFF


# ---------------------------------------------------------------------------
# Header key derivation (offset 4096 -> info[8])
# ---------------------------------------------------------------------------

def header_kdf(file_data, offset=4096):
    """Derive the 8-dword info table from the encrypted header cells.

    info[0] is stored directly; every following cell is XORed with a rolling
    key that mixes in the cell value and the square of the index.
    """
    info = [0] * 8
    info[0] = get_u32(file_data, offset)
    k = info[0]
    for i in range(7):
        cell = get_u32(file_data, offset + 4 + 4 * i)
        info[i + 1] = k ^ cell
        k = (i * i) ^ ((k + cell - i) & MASK32)
    return info


# ---------------------------------------------------------------------------
# Rolling XOR chain over the payload body
# ---------------------------------------------------------------------------

def payload_xor_chain(file_data, out, info, decrypt_size):
    """Decrypt the bulk of the payload into the image buffer.

    Same rolling-key family as the header KDF, but the key is seeded from
    info[0] and the complement of the decrypted size, and advances with +i.
    """
    base_src = (info[4] + 4096) & MASK32
    k = (info[0] + (~decrypt_size & MASK32)) & MASK32
    for i in range(decrypt_size >> 2):
        cell = get_u32(file_data, (base_src + 4 * i) & MASK32)
        put_u32(out, (info[3] + 4 * i) & MASK32, k ^ cell)
        k = (i * i) ^ ((k + cell + i) & MASK32)


# ---------------------------------------------------------------------------
# XOR + rotate-right dword cipher (rolling key), shift 19 or 21
# ---------------------------------------------------------------------------

def xor_ror_dwords(d, pos, key, shift):
    """Decrypt a dword region described by the (addr, len) pair at `pos`.

    Used to unwrap each stage's pointer block. The key rolls forward by the
    loop index; the index is also subtracted after the rotation.
    """
    base_addr = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    for i in range(length >> 2):
        off = (base_addr + 4 * i) & MASK32
        v = get_u32(d, off) ^ key
        key = (key + i) & MASK32
        put_u32(d, off, (ror32(v, shift) - i) & MASK32)


# ---------------------------------------------------------------------------
# Triple byte-rotate ciphers with two rolling keys
# ---------------------------------------------------------------------------

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
    """Position-keyed variant: rotate by 2, keyed from the address itself.

    Each output byte depends only on the input byte and the low 8 bits of its
    address, so any 4 bytes can be trial-decrypted without touching the rest
    of the buffer - a property the loader's table walks rely on.
    """
    b = va & 0xFF
    b2 = (b + 1) & 0xFF
    for i in range(size):
        idx = va + i
        x = rol8(d[idx], 2) ^ b2
        x = rol8(x, 2) ^ b
        d[idx] = rol8(x, 2)
        b = (b + 1) & 0xFF
        b2 = (b2 + 1) & 0xFF


def trial_byte_rotate2(d, va):
    """Non-mutating 4-byte trial decrypt (relies on the no-cross-byte-state
    property of byte_rotate2). Used to peek at encrypted descriptors."""
    out = bytearray(4)
    for i in range(4):
        b = (va + i) & 0xFF
        x = rol8(d[va + i], 2) ^ ((b + 1) & 0xFF)
        x = rol8(x, 2) ^ b
        out[i] = rol8(x, 2)
    return get_u32(out, 0)


# ---------------------------------------------------------------------------
# LFSR keystream (protects the embedded bytecode stubs)
# ---------------------------------------------------------------------------

def lfsr_keystream(n):
    """n bytes of the LFSR keystream: seed 1, feedback 0x8003, 8 bits per
    output byte, LSB first. The stream is data-independent and can be
    replayed at any position."""
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


# ---------------------------------------------------------------------------
# Import-name string cipher
# ---------------------------------------------------------------------------

def string_cipher(d, pos, key):
    """Decrypt a NUL-terminated string in place: nibble swap, rolling
    subtract (step 67). The initial key is the low byte of the string RVA."""
    i = 0
    while d[pos + i] != 0:
        b = ror8(d[pos + i], 4)
        b = (b - key) & 0xFF
        if b == 0:
            b = (-key) & 0xFF
        d[pos + i] = b
        key = (key + 67) & 0xFF
        i += 1


# ---------------------------------------------------------------------------
# Per-page .text scramble
# ---------------------------------------------------------------------------

def page_scramble(d, va, size, key):
    """XOR one byte per 16-byte block across a page. Block 0 only advances
    the key. `key` is the page index shifted left by a build-specific amount
    (0 or 15)."""
    for i in range(size >> 4):
        mixed = (ror32(key, 15) + i) & MASK32
        key = (mixed + i) & MASK32
        if i == 0:
            continue
        d[va + i * 16 + (mixed & 0xF)] ^= key & 0xFF


def page_scramble_pe32(d, pa, page, big_formula):
    """32-bit build variant. The page key is either (page+1) or
    0x8000*(page+1); the formula is not recorded anywhere in the file."""
    key = (0x8000 * (page + 1)) & MASK32 if big_formula else page + 1
    key = ror32(key, 15)
    for bi in range(1, 256):
        rk = ror32(key, 15)
        ri = (rk + bi) & MASK32
        key = (ri + bi) & MASK32
        d[pa + bi * 16 + (ri & 0xF)] ^= key & 0xFF


# ---------------------------------------------------------------------------
# On-demand page cipher (runtime page-fault handler)
# ---------------------------------------------------------------------------

def demand_page_key(page_va, region_base, key_part):
    """Mix the faulting page VA, the region base, and per-page key material."""
    return ((page_va + region_base) ^ key_part) & MASK32


def demand_page_decrypt(buf, key):
    """In-place dword cipher used after a PAGE_NOACCESS fault.

    `buf` is the 4 KiB ciphertext page (or any multiple of 4 bytes). `key`
    is `demand_page_key(...)`. Each dword is XORed with the previous
    ciphertext dword and a rolling state that starts as
    `(key << 16) ^ key` and advances with `rol32(state + i, 3)`.
    """
    count = len(buf) >> 2
    state = ((key << 16) ^ key) & MASK32
    prev = state
    for i in range(count):
        enc = get_u32(buf, i * 4)
        state = rol32((state + i) & MASK32, 3)
        put_u32(buf, i * 4, enc ^ prev ^ state)
        prev = enc


# ---------------------------------------------------------------------------
# CRC-32 (standard reflected polynomial 0xEDB88320)
# ---------------------------------------------------------------------------

def _build_crc_table():
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = 0xEDB88320 ^ (c >> 1) if c & 1 else c >> 1
        table.append(c)
    return table


_CRC_TABLE = _build_crc_table()


def crc32_append(initial, data):
    crc = ~initial & MASK32
    for b in data:
        crc = _CRC_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return ~crc & MASK32


def crc32(data):
    return crc32_append(0, data)


def calculate_checksum(d, pos):
    """crc32(region) ^ length, where (offset, length) is read from d[pos]."""
    offset = get_u32(d, pos)
    length = get_u32(d, pos + 4)
    return crc32(d[offset:offset + length]) ^ length


# ---------------------------------------------------------------------------
# Triangular-number key schedule (stage key "advance")
# ---------------------------------------------------------------------------

def advance_key(key, iterations):
    """Roll a stage key forward: for m in 0..iterations, add every integer
    1..(m+1)*100. The constants make each stage's key depend on content
    that only exists after the previous stage decrypted correctly."""
    for m in range(iterations):
        bound = ((m + 1) * 25) << 2
        for n in range(1, bound + 1):
            key = (key + n) & MASK32
    return key
```
