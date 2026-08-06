---
description: Crackproof 施加于受保护内容的完整数据变换族——密码、压缩格式、字节码置换与校验和链，附经测试的实现。
---

# 数据变换原语

容器的每一层都由一小组原语构成。一旦逐个定义清楚，分阶段加载器就只是“在偏移 X 处以密钥 Y 调用原语 N”的严格有序重复。本页精确定义每个原语，并给出 Python 实现。

{% hint style="success" %}
本页所有代码片段都已实际执行并与受保护二进制中实现的算法核对：每个函数的输出都在相同输入上与参考移植逐字节比对一致。
{% endhint %}

## 约定

所有缓冲区都是可变字节数组（`bytearray`）；原始算法原地工作。全文使用的辅助函数：

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

## 滚动密钥家族

两个密码共享同一滚动密钥设计：密钥从种子开始，每个单元与当前密钥异或，随后密钥混入单元值、循环索引与索引平方向前滚动。头部 KDF（见受保护文件格式）是 8 单元实例；payload 主体密码是同族的长形式，种子与更新规则不同：

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

由于密钥逐 dword 向前滚动，该链必须从头开始解——不重放整条链就无法对 payload 做随机访问。

## XOR + 循环右移 dword 密码

这个密码用于解开每个阶段的指针块。它从缓冲区自身读出 `(base_addr, length)` 描述符，然后变换每个 dword：与滚动密钥异或、按固定移位量循环右移、再减去循环索引。移位量按调用点取 19 或 21。

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

32 位构建还会对其中一个阶段在候选集 `[19, 21, 17, 23, 15, 25, 13, 11]` 上爆破移位量，接受输出能解析为合法阶段表的那个（见分阶段加载器）。

## 三重字节旋转密码

两个字节密码共享同一结构：每字节三次位旋转，旋转之间异或两个滚动密钥字节。它们的区别在于旋转量与初始密钥的派生方式。

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

位置密钥变体有一个加载器各表遍历重度依赖的性质：**每个输出字节只依赖输入字节与其地址的低 8 位**——无跨字节状态。因此任意 4 字节都可以在不触碰缓冲区其余部分的情况下试解：

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

加载器中贯穿始终的 16 字节描述符都用 `byte_rotate2` 加密，按位置串联：每个描述符的密钥来自其自身地址，遍历在长度字段为零时终止。

## LFSR 密钥流

按构建定制的字节码 stub（见下文）本身还包着一层 LFSR 密钥流。该流与数据无关——种子 1、反馈多项式 `0x8003`、每字节吐 8 位、LSB 优先——因此可在任意位置重放，这使得对候选 stub 位置做试解码代价很低：

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

一个 stub 块占固定的 96 字节槽；`pos + 95` 处的字节是内部程序的（未加密）长度。

## 导入名字符串密码

DLL 名与导入函数名用一个滚动字节密码加密：半字节交换、减密钥、密钥步进 67。初始密钥是字符串 RVA 的低字节——不知道名字的位置就无法解密它。

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

`b == 0` 的重映射避免在字符串中间产生 NUL（那会截断遍历）：若减法结果为零，该字节改为取密钥的二进制补码。

## 页级代码扰动

可执行节在一切之上还带一层稀疏的页粒度扰动：每 16 字节块 XOR 一个字节，块内偏移随块变化。模式跳过块 0（但其密钥状态仍推进）。每页 4096 字节中有 255 个被触及。

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
移位量（64 位：0 或 15）与公式选择（32 位：`page+1` 或 `0x8000*(page+1)`）**不记录在文件的任何字段里**。两个构建可以携带逐字节相同的配置戳却需要不同选择。唯一可靠的判别依据是代码内容本身：在每个候选下对采样页重放扰动，统计有多少位置解码为 `0xCC`（MSVC 的 `int3` 填充字节）。正确选择会不成比例地还原填充；错误选择则每 16 字节约搅乱 1 字节。某些模块（原生 DLL）代码是明文，绝不能做反扰动。
{% endhint %}

## CRC-32 校验和

校验和使用标准反射 CRC-32（多项式 `0xEDB88320`，即 zlib/以太网 CRC——`crc32(b"123456789") == 0xCBF43926`）。出现两种描述符形式：

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

第二种形式以滚动初值链式覆盖**原始文件字节**（用上一次结果作 `initial` 调用 `crc32_append`），用于分阶段加载器中那条只用于校验的遍历。

## 三角数密钥调度

若干阶段密钥通过累加结构化整数级数来“推进”——每轮把 1 到 `(m+1) * 100` 的每个整数都加上：

```python
def advance_key(key, iterations):
    for m in range(iterations):
        bound = ((m + 1) * 25) << 2
        for n in range(1, bound + 1):
            key = (key + n) & MASK32
    return key
```

种子是从刚解密的前一阶段读出的内容，所以只有之前的一切都解密正确，推进后的密钥才会正确——这是防篡改设计的一半（另一半是本页末尾的校验和链）。

## 分组密码：内嵌密钥调度的 AES-CBC

大块内容——阶段与节数据块——以 CBC 模式的 AES 解密保护。两个设计选择值得注意：

* **密钥调度表就存在数据缓冲区内部。** `key_offset` 处有一个小头部存放轮数（`key_offset + 2` 处的小端 u16），其后是 `(rounds + 1)` 个 16 字节轮密钥。没有独立密钥材料可提取；调度表随其他一切一并解出。
* **这些表是标准的 AES 解密 T 表**（InvSubBytes 融合 InvMixColumns），下面由 GF(2⁸) 运算生成——公开的 AES 常量，并非专有数据。状态字按大端读写。

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

每个分组经 `_aes_round` 解密（初始密钥异或、`rounds − 1` 轮 T 表轮变换、以及仅含 SubBytes/ShiftRows 的末轮——教科书式 AES 逆结构），再与前一组密文异或（零 IV）。

## Huffman/LZ 压缩格式

多数 payload 块用一种定制混合格式压缩：Huffman 编码的 token 流，token 分字面量、游程填充与 LZ 回拷三类。解码表随数据同行，位于同一缓冲区的 `key_offset` 处。

**表格式。** 表是 3 字节表项构成的森林：一个 u16 符号/子节点字段与一个 u8 码长字段。根选择读 8 位输入作为表项索引。最高位（`0x8000`）标记叶子；内部节点存储兄弟节点对中首个的索引，再多读 1 位输入在二者间选择。存储的长度字节累计迄今消耗的位数（根为 8），因此走过 N 层内部节点到达的叶子，其总码长为 8 + N 位。

**token 格式。** token 的 8–9 位选择模式，0–7 位是载荷：

| 模式      | 含义                                                  |
| ------- | --------------------------------------------------- |
| `0x000` | 字面量：输出载荷字节                                          |
| `0x100` | 计数累加器：把载荷拼进一个大端 pending 值（本身不输出）                    |
| `0x200` | 游程填充：把刚写出的 1/2/4 字节单元重复 `pending × payload` 次       |
| `0x300` | LZ 回拷：从输出游标前 `pending + payload` 字节处拷贝 `payload` 字节 |

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

布尔返回值是损坏信号——而且重要的是，它还是一个**判定器（oracle）**：当容器没有记录某个密钥或移位选择时，就逐个尝试候选，直到某个能干净解压为止。分阶段加载器中有多处这样的“试解-验证”点。

## 按构建定制的字节码置换

最有辨识度的一层：Crackproof 不为 payload 数据硬编码固定的逐字节变换。加壳时它**为每个构建生成一段独有的 x86 stub**——一个在 `AL` 中接收一个字节、施加一小段随机算术/移位指令序列后返回的函数。加载器在分组密码之后、解压之前，对 payload 的每个字节运行这段 stub。因此来自不同构建的两个受保护文件不共享任何 payload 置换。

stub 以上述 LFSR 密钥流包裹存储。不执行 x86，而是把指令字节解码成小 op 列表并解释执行——实际出现的指令只有一个很窄的子集：

| 字节         | x86 指令         | VM 操作          |
| ---------- | -------------- | -------------- |
| `04 ib`    | `ADD AL, imm8` | `("add", imm)` |
| `2C ib`    | `SUB AL, imm8` | `("sub", imm)` |
| `34 ib`    | `XOR AL, imm8` | `("xor", imm)` |
| `90`       | `NOP`          | 跳过             |
| `C0 /0 ib` | `ROL AL, imm8` | `("rol", imm)` |
| `C0 /1 ib` | `ROR AL, imm8` | `("ror", imm)` |
| `FE /0`    | `INC AL`       | `("inc",)`     |
| `FE /1`    | `DEC AL`       | `("dec",)`     |
| `C3`       | `RET`          | 程序结束           |

对 `C0`/`FE`，ModR/M 字节必须编码寄存器直接寻址的 `AL`（`mod=3, rm=0`）；reg 字段选择子操作。其余一律解析失败——正是这种严格性让候选 stub 位置的试解码可靠：解出的垃圾数据几乎不可能解析为以 `RET` 结尾的合法程序。

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

由此直接得到两个结构性质：

* **整条链是 256 字节值空间上的一个置换。** 每个 op 都可逆（`add↔sub`、`xor` 自逆、`rol↔ror`、`inc↔dec`），所以整个映射是双射。可以预计算成一张 256 项翻译表（`bytes(apply_ops(ops, i) for i in range(256))`）；沿 op 列表逆序、每个 op 换成其逆 op，即得逆链。
* **定位 stub 是搜索问题，而非固定偏移。** 由于密钥流与数据无关，对候选位置做试 XOR 并解析即可；能解码为合法程序（含足够真实操作、以 `RET` 终止）的最低位置就是真 stub。更靠后的合法解析多是尾部填充字节的巧合解码。

一个构建携带**两个**这样的 stub：一个用于解密最终加载器阶段，另一个独立的应用于每个节数据块。

## 校验和链

最后一个原语不是密码，而是密钥的组合方式。一个阶段的解密密钥通常形如：

```
stage_key = xor_accumulator ^ crc32_checksum_of_earlier_content ^ content_derived_seed
```

* **xor 累加器**：遍历一张 `(offset, length)` 区域描述符表，把各项的 `calculate_checksum` 值异或累积。
* **校验和**：对只有在前序阶段正确解密后才以明文存在的字节做 CRC-32。
* **种子**：从刚解密的内容读出的一个 dword，通常再经 `advance_key` 推进。

其结果是：各阶段无法乱序解密；上游任何一字节被改动，下游由它派生的所有密钥全部报废。这条链是容器的防篡改机制——反过来，它也使得解包结果可验证：任何一处选择出错，后续阶段都解不开，而不是产生隐性的错误结果。各构建家族如何组合这些要素，正是下一页的主题。
