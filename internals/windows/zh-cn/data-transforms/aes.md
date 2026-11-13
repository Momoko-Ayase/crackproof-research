---
description: "使用映像内嵌扩展轮密钥表与 T 表逆轮函数的零 IV AES-CBC 解密。"
icon: key
---

# AES-CBC 解密层

## 基于缓冲区内嵌轮密钥表的 AES-CBC

Stage 3 至 Stage 5 以及压缩节数据块均通过零 IV 的 AES-CBC 解密，其扩展轮密钥表直接存放在工作映像缓冲区内部：

* **缓冲区内嵌轮密钥表：** `key_offset` 起始处为 4 字节头部，其中 `key_offset + 2` 处的小端序 `u16` 给出轮数（`10`、`12` 或 `14`），紧随其后的 `key_offset + 4` 处存放 `(rounds + 1)` 组 16 字节解密轮密钥。
* **标准 GF(2⁸) 逆 T 表：** 中间轮将 `InvSubBytes`、`InvShiftRows` 与 `InvMixColumns`（约化多项式 `0x1B`，系数 `0x0B`、`0x0D`、`0x09`、`0x0E`）合并为四张 256 项 `u32` 查找表；末轮执行 `InvSubBytes` 并按 `InvShiftRows` 重排字节位置（首字取 `n0 | n3 | n2 | n1` 对应字节，其余三字依次循环轮换）。状态字均按大端序加载和写回。

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

每个 16 字节分组依次执行初始轮密钥异或、`rounds - 1` 轮等价逆密码（Equivalent Inverse Cipher）T 表查表与末轮 `InvSubBytes`/`InvShiftRows` 变换，最后与上一组密文块（`prev`，初始为 16 个零字节）按字节异或。
