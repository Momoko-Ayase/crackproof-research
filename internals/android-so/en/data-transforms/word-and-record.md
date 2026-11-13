---
description: "GF(2^32) word multiplication, stream-header and record-descriptor ciphers, and the 0x9D protected descriptor."
icon: rotate
---

# Word, stream, and record ciphers

Android streams replace the Windows rolling-XOR primitives with GF(2³²) multiplication and 32-bit modular arithmetic across stream headers, `0x5C`-byte record descriptors, and the `0x9D` protected descriptor.

## GF(2³²) fixed multiplication

`gf32_mul_fixed(value)` masks its input to 32 bits and multiplies it by `0x94511DD2` in GF(2³²) modulo `0x579357EB`:

```text
MASK32 = 0xFFFFFFFF

def gf32_mul_fixed(value):
    value &= MASK32
    multiplier = 0x94511DD2
    result = 0
    while multiplier:
        if multiplier & 1:
            result ^= value
        carry = value >> 31
        value = (value << 1) & MASK32
        if carry:
            value ^= 0x579357EB
        multiplier >>= 1
    return result
```

In the stream, descriptor, and [container header](container.md) formulas, `gf(x)` denotes `gf32_mul_fixed(x)`.

## Stage 1 word cipher

Both the 32-byte Stage 1 parameter header and the encrypted Stage 2 image use unsigned 32-bit wraparound for word index `i` and family constant `C` (`0xBF20165D` or `0xBF189BDD`):

```text
plain[i] = ((cipher[i] + (i + 3) * key) ^ (C * (i + 1))) & MASK32
```

In the 32-byte parameter header, word `0` provides `key = cipher[0] ^ C` and is written back as `plain[0] = key` once words `1..7` are decoded. Header field invariants are documented on [Stage 1 header](../file-format/stage1.md).

## Stream-header cipher

Every interpreter stream (`0xE2` at the root, `0xE3`..`0xE8` at nested levels) begins with two little-endian dwords (`cipher0`, `cipher1`). Two constant families have been observed; both mask intermediate products and sums to 32 bits and derive `dw0` (record count) and `G` (the stream's descriptor seed):

{% tabs %}
{% tab title="Family A" %}
```text
K   = (sid * 0x9D323CD7) & MASK32
K   = ((K << (sid & 0xB)) + (K >> (sid & 7))) & MASK32
dw0 = (gf((cipher0 + 0xCBF0C1D8) & MASK32) ^ ((K + 0x4178CB33) & MASK32)) & MASK32
dw1 = (gf((cipher0 + cipher1) & MASK32)    ^ ((K + 0xF119421B) & MASK32)) & MASK32
G   = (K + 0x5590AD79 + dw1) & MASK32
```
{% endtab %}

{% tab title="Family B" %}
```text
K   = (sid * 0x9D323CD7) & MASK32
mix = ((K >> (sid & 7)) + 0x5E727D74) & MASK32
mix = (mix + ((K << (sid & 0xB)) & MASK32) + 0xF71E3005) & MASK32
dw0 = (gf((cipher0 + 0xCBF0C1D8) & MASK32) ^ ((0xEBE81DBA + mix) & MASK32)) & MASK32
dw1 = (gf((cipher1 + cipher0) & MASK32)    ^ ((0xEBE81DBA * 5 + mix) & MASK32)) & MASK32
G   = (dw1 + mix) & MASK32
```
{% endtab %}
{% endtabs %}

Both families are tried against the structural descriptor checks in [Stage 2 streams](../file-format/stage2-streams.md).

## Record-descriptor cipher

Each `0x5C`-byte record descriptor consists of 23 little-endian dwords. Given stream seed `G` and zero-based record index `idx`, both families share the same decryption loop:

```text
def rec_decrypt(G, idx, rec):
    product = ((G + 0x96F60B71) * G) & MASK32
    record_mask = (product << ((idx + 1) & 3)) & MASK32
    stream_mix = (G * 0x06A55BCC + product) & MASK32
    feedback = 0xF02F7685
    acc = 0x79934CF6
    for off in range(0, 0x5C, 4):
        cipher = get_u32(rec, off)
        square = (feedback * feedback) & MASK32
        value = gf32_mul_fixed(cipher ^ (square >> 3))
        value = (value ^ record_mask) & MASK32
        value = (value + acc + G) & MASK32
        value = (value - (stream_mix >> ((off + 3) & 5))) & MASK32
        put_u32(rec, off, value)
        acc = (acc + 0xE64D33D8) & MASK32
        feedback = cipher
```

{% hint style="warning" %}
`off` advances by 4 bytes per iteration, so `(off + 3) & 5` alternates between `1` (even words: `(0 + 3) & 5 = 1`) and `5` (odd words: `(4 + 3) & 5 = 5`). `feedback` is updated with the raw ciphertext word `cipher`, not the decrypted `value`.
{% endhint %}

## The `0x9D` protected descriptor

Direct module `0x9D` starts with a `0x5C`-byte `ProtectedDescriptor` encrypted under `header_seed` from [module `0x9B`](module-config.md):

```text
def decrypt_protected_descriptor(data, seed):
    base0 = ((seed + 0xD3E87144) * seed) & MASK32
    base1 = (base0 + seed * 0x0BD9418D) & MASK32
    words = [0] * (0x5C // 4)
    for i in range(len(words)):
        cipher = get_u32(data, i * 4)
        sub = (base0 << (4 if i & 1 else 0)) & MASK32
        words[i] = ((cipher - sub) ^ (base1 >> ((seed + i * 4) & 7))) & MASK32
    return words
```

Validated plaintext requires `words[0] == 0x9D` (`command_id`), `words[2] == 0x5C` (`outer_offset`, immediately after the descriptor), and `words[6..23] == 0`. Words `2..5` give `(outer_offset, outer_size)` for the primary ELF image container and `(aux_offset, aux_size)` for the auxiliary relocation/symbol container described in [Container transforms](container.md).
