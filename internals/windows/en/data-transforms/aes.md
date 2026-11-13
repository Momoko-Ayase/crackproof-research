---
description: "Zero-IV AES-CBC decryption using an in-buffer expanded key schedule and T-table inverse rounds."
icon: key
---

# AES-CBC layer

## AES-CBC with an in-buffer key schedule

Stages 3 through 5 and compressed section blocks pass through zero-IV AES-CBC decryption using a schedule stored inside the working image buffer itself:

* **In-buffer schedule:** `key_offset` starts with a 4-byte header whose little-endian `u16` at `key_offset + 2` gives the round count (`10`, `12`, or `14`), followed immediately at `key_offset + 4` by `(rounds + 1)` 16-byte decryption round keys.
* **Standard GF(2⁸) inverse T-tables:** middle rounds fuse `InvSubBytes`, `InvShiftRows`, and `InvMixColumns` (polynomial `0x1B`, multipliers `0x0B`, `0x0D`, `0x09`, `0x0E`) into four 256-entry `u32` tables, while the final round applies `InvSubBytes` with the `InvShiftRows` byte lane permutation (`n0 | n3 | n2 | n1` rotated across words). State words load and store big-endian.

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

Each 16-byte block runs initial round-key XOR, `rounds - 1` Equivalent Inverse Cipher T-table rounds, and the final `InvSubBytes`/`InvShiftRows` round before XORing with the previous ciphertext block (`prev`, initialized to 16 zero bytes).
