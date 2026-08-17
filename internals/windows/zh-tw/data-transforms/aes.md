---
description: "AES-CBC 層及其存放在緩衝區內的擴展密鑰表。"
---

# AES-CBC 層

## 分組密碼：內嵌密鑰調度的 AES-CBC

大塊內容——階段與節數據塊——以 CBC 模式的 AES 解密保護。兩個設計選擇值得注意：

- **密鑰調度表就存在數據緩衝區內部。** `key_offset` 處有一個小頭部存放輪數（`key_offset + 2` 處的小端 u16），其後是 `(rounds + 1)` 個 16 字節輪密鑰。沒有獨立密鑰材料可提取；調度表隨其他一切一併解出。
- **這些表是標準的 AES 解密 T 表**（InvSubBytes 融合 InvMixColumns），下面由 GF(2⁸) 運算生成——公開的 AES 常量，並非專有數據。狀態字按大端讀寫。

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

每個分組經 `_aes_round` 解密（初始密鑰異或、`rounds − 1` 輪 T 表輪變換、以及僅含 SubBytes/ShiftRows 的末輪——教科書式 AES 逆結構），再與前一組密文異或（零 IV）。

