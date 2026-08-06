---
description: "The independent reference port of the algorithms; compiles to a program that prints ground-truth vectors."
---

# `rust_vectors.rs`

The reference port used to produce the ground-truth vectors. Every primitive is a direct transcription of the algorithms as implemented in protected binaries. Build it with `rustc -O rust_vectors.rs` and run it to regenerate `vectors.txt`.

```rust
// Vector generator for the CrackProof research documentation.
// Every primitive below is copied VERBATIM from a reference port of the
// algorithms as implemented in protected binaries, so the printed vectors
// are authoritative ground truth for the Python snippets in the docs.

// ---------------------------------------------------------------------------
// Byte-order accessors (primitives.rs)
// ---------------------------------------------------------------------------

fn get_u16(data: &[u8], offset: u32) -> u16 {
    let i = offset as usize;
    u16::from_le_bytes([data[i], data[i + 1]])
}

fn get_u32(data: &[u8], offset: u32) -> u32 {
    let i = offset as usize;
    u32::from_le_bytes([data[i], data[i + 1], data[i + 2], data[i + 3]])
}

fn write_u32(data: &mut [u8], offset: u32, value: u32) {
    let i = offset as usize;
    let b = value.to_le_bytes();
    data[i] = b[0];
    data[i + 1] = b[1];
    data[i + 2] = b[2];
    data[i + 3] = b[3];
}

fn write_u16(data: &mut [u8], offset: u32, value: u32) {
    let i = offset as usize;
    let v = value as u16;
    let b = v.to_le_bytes();
    data[i] = b[0];
    data[i + 1] = b[1];
}

// ---------------------------------------------------------------------------
// CRC32 (crc32.rs)
// ---------------------------------------------------------------------------

const fn build_crc_table() -> [u32; 256] {
    let mut table = [0u32; 256];
    let mut i = 0;
    while i < 256 {
        let mut c = i as u32;
        let mut k = 0;
        while k < 8 {
            c = if c & 1 != 0 {
                0xEDB8_8320 ^ (c >> 1)
            } else {
                c >> 1
            };
            k += 1;
        }
        table[i] = c;
        i += 1;
    }
    table
}

const CRC_TABLE: [u32; 256] = build_crc_table();

fn crc_append(initial: u32, data: &[u8]) -> u32 {
    let mut crc = !initial;
    for &b in data {
        crc = CRC_TABLE[((crc ^ b as u32) & 0xFF) as usize] ^ (crc >> 8);
    }
    !crc
}

fn crc_compute(data: &[u8]) -> u32 {
    crc_append(0, data)
}

// ---------------------------------------------------------------------------
// AES inverse tables (tables.rs) — generated at compile time
// ---------------------------------------------------------------------------

const fn gf_mul(mut a: u8, mut b: u8) -> u8 {
    let mut p: u8 = 0;
    let mut i = 0;
    while i < 8 {
        if b & 1 != 0 {
            p ^= a;
        }
        let hi = a & 0x80;
        a <<= 1;
        if hi != 0 {
            a ^= 0x1B;
        }
        b >>= 1;
        i += 1;
    }
    p
}

const fn inv_sbox() -> [u8; 256] {
    let mut inv = [0u8; 256];
    let mut a = 1usize;
    while a < 256 {
        let mut b = 1usize;
        while b < 256 {
            if gf_mul(a as u8, b as u8) == 1 {
                inv[a] = b as u8;
                break;
            }
            b += 1;
        }
        a += 1;
    }
    let mut sb = [0u8; 256];
    let mut i = 0usize;
    while i < 256 {
        let mut x = inv[i];
        let mut s = inv[i];
        let mut r = 0;
        while r < 4 {
            s = s.rotate_left(1);
            x ^= s;
            r += 1;
        }
        sb[i] = x ^ 0x63;
        i += 1;
    }
    let mut isb = [0u8; 256];
    let mut i = 0usize;
    while i < 256 {
        isb[sb[i] as usize] = i as u8;
        i += 1;
    }
    isb
}

struct AesTables {
    cm1: [u8; 1024],
    cm2: [u8; 1024],
    cm3: [u8; 1024],
    cm4: [u8; 1024],
    sbox: [u8; 1024],
}

const fn build_tables() -> AesTables {
    let isb = inv_sbox();
    let mut cm1 = [0u8; 1024];
    let mut cm2 = [0u8; 1024];
    let mut cm3 = [0u8; 1024];
    let mut cm4 = [0u8; 1024];
    let mut sbox = [0u8; 1024];
    let mut x = 0usize;
    while x < 256 {
        let s = isb[x];
        let mut j = 0;
        while j < 4 {
            sbox[x * 4 + j] = s;
            cm1[x * 4 + j] = [
                gf_mul(0x0b, s),
                gf_mul(0x0d, s),
                gf_mul(0x09, s),
                gf_mul(0x0e, s),
            ][j];
            cm2[x * 4 + j] = [
                gf_mul(0x0d, s),
                gf_mul(0x09, s),
                gf_mul(0x0e, s),
                gf_mul(0x0b, s),
            ][j];
            cm3[x * 4 + j] = [
                gf_mul(0x09, s),
                gf_mul(0x0e, s),
                gf_mul(0x0b, s),
                gf_mul(0x0d, s),
            ][j];
            cm4[x * 4 + j] = [
                gf_mul(0x0e, s),
                gf_mul(0x0b, s),
                gf_mul(0x0d, s),
                gf_mul(0x09, s),
            ][j];
            j += 1;
        }
        x += 1;
    }
    AesTables {
        cm1,
        cm2,
        cm3,
        cm4,
        sbox,
    }
}

const TABLES: AesTables = build_tables();

// ---------------------------------------------------------------------------
// AES round + CBC decrypt (primitives.rs, verbatim)
// ---------------------------------------------------------------------------

fn aes_round(d: &mut [u8], pos: u32, key_offset: u32, round: u32) {
    let cm1 = &TABLES.cm1;
    let cm2 = &TABLES.cm2;
    let cm3 = &TABLES.cm3;
    let cm4 = &TABLES.cm4;
    let sbox = &TABLES.sbox;

    let mut n0 = get_u32(d, pos).swap_bytes() ^ get_u32(d, key_offset);
    let mut n1 =
        get_u32(d, pos.wrapping_add(4)).swap_bytes() ^ get_u32(d, key_offset.wrapping_add(4));
    let mut n2 =
        get_u32(d, pos.wrapping_add(8)).swap_bytes() ^ get_u32(d, key_offset.wrapping_add(8));
    let mut n3 =
        get_u32(d, pos.wrapping_add(12)).swap_bytes() ^ get_u32(d, key_offset.wrapping_add(12));

    let mut r = 1u32;
    while r < round {
        let off = key_offset.wrapping_add(r.wrapping_mul(16));
        let a = get_u32(cm2, ((n3 >> 16) & 0xFF) * 4)
            ^ get_u32(cm3, ((n2 >> 8) & 0xFF) * 4)
            ^ get_u32(cm1, ((n0 >> 24) & 0xFF) * 4)
            ^ get_u32(cm4, (n1 & 0xFF) * 4)
            ^ get_u32(d, off);
        let b = get_u32(cm2, ((n0 >> 16) & 0xFF) * 4)
            ^ get_u32(cm1, ((n1 >> 24) & 0xFF) * 4)
            ^ get_u32(cm3, ((n3 >> 8) & 0xFF) * 4)
            ^ get_u32(cm4, (n2 & 0xFF) * 4)
            ^ get_u32(d, off.wrapping_add(4));
        let c = get_u32(cm2, ((n1 >> 16) & 0xFF) * 4)
            ^ get_u32(cm3, ((n0 >> 8) & 0xFF) * 4)
            ^ get_u32(cm1, ((n2 >> 24) & 0xFF) * 4)
            ^ get_u32(cm4, (n3 & 0xFF) * 4)
            ^ get_u32(d, off.wrapping_add(8));
        let e = get_u32(cm3, ((n1 >> 8) & 0xFF) * 4)
            ^ get_u32(cm2, ((n2 >> 16) & 0xFF) * 4)
            ^ get_u32(cm1, ((n3 >> 24) & 0xFF) * 4)
            ^ get_u32(cm4, (n0 & 0xFF) * 4)
            ^ get_u32(d, off.wrapping_add(12));
        n0 = a;
        n1 = b;
        n2 = c;
        n3 = e;
        r = r.wrapping_add(1);
    }

    let s0 = (get_u32(sbox, ((n0 >> 24) & 0xFF) * 4) & 0xFF00_0000)
        | (get_u32(sbox, ((n3 >> 16) & 0xFF) * 4) & 0x00FF_0000)
        | (get_u32(sbox, ((n2 >> 8) & 0xFF) * 4) & 0x0000_FF00)
        | (get_u32(sbox, (n1 & 0xFF) * 4) & 0x0000_00FF);
    let s1 = (get_u32(sbox, ((n1 >> 24) & 0xFF) * 4) & 0xFF00_0000)
        | (get_u32(sbox, ((n0 >> 16) & 0xFF) * 4) & 0x00FF_0000)
        | (get_u32(sbox, ((n3 >> 8) & 0xFF) * 4) & 0x0000_FF00)
        | (get_u32(sbox, (n2 & 0xFF) * 4) & 0x0000_00FF);
    let s2 = (get_u32(sbox, ((n2 >> 24) & 0xFF) * 4) & 0xFF00_0000)
        | (get_u32(sbox, ((n1 >> 16) & 0xFF) * 4) & 0x00FF_0000)
        | (get_u32(sbox, ((n0 >> 8) & 0xFF) * 4) & 0x0000_FF00)
        | (get_u32(sbox, (n3 & 0xFF) * 4) & 0x0000_00FF);
    let s3 = (get_u32(sbox, ((n3 >> 24) & 0xFF) * 4) & 0xFF00_0000)
        | (get_u32(sbox, ((n2 >> 16) & 0xFF) * 4) & 0x00FF_0000)
        | (get_u32(sbox, ((n1 >> 8) & 0xFF) * 4) & 0x0000_FF00)
        | (get_u32(sbox, (n0 & 0xFF) * 4) & 0x0000_00FF);

    let last = key_offset.wrapping_add(round.wrapping_mul(16));
    n0 = s0 ^ get_u32(d, last);
    n1 = s1 ^ get_u32(d, last.wrapping_add(4));
    n2 = s2 ^ get_u32(d, last.wrapping_add(8));
    n3 = s3 ^ get_u32(d, last.wrapping_add(12));

    write_u32(d, pos, n0.swap_bytes());
    write_u32(d, pos.wrapping_add(4), n1.swap_bytes());
    write_u32(d, pos.wrapping_add(8), n2.swap_bytes());
    write_u32(d, pos.wrapping_add(12), n3.swap_bytes());
}

fn aes_decrypt(d: &mut [u8], pos: u32, size: u32, key_offset: u32) {
    let mut prev = [0u8; 16];
    let mut cur = [0u8; 16];
    let round = get_u16(d, key_offset.wrapping_add(2)) as u32;
    let blocks = size >> 4;
    for i in 0..blocks {
        let p = pos.wrapping_add(i.wrapping_mul(16));
        let pi = p as usize;
        cur.copy_from_slice(&d[pi..pi + 16]);
        aes_round(d, p, key_offset.wrapping_add(4), round);
        for j in 0..16 {
            d[pi + j] ^= prev[j];
        }
        prev = cur;
    }
}

// ---------------------------------------------------------------------------
// Decrypt primitives (primitives.rs / exe.rs, verbatim)
// ---------------------------------------------------------------------------

fn decrypt_data1(file_data: &[u8], info: &mut [u32; 8]) {
    info[0] = get_u32(file_data, 4096);
    let mut k = get_u32(file_data, 4096);
    for i in 0..7u32 {
        let off = i.wrapping_mul(4).wrapping_add(4);
        let cell = get_u32(file_data, 4096u32.wrapping_add(off));
        info[(i + 1) as usize] = k ^ cell;
        k = i.wrapping_mul(i) ^ (k.wrapping_add(cell).wrapping_sub(i));
    }
}

fn decrypt_data3(d: &mut [u8], pos: u32, mut key: u32, shift: u32) {
    let base_addr = get_u32(d, pos);
    let length = get_u32(d, pos.wrapping_add(4));
    let words = length >> 2;
    for i in 0..words {
        let off = base_addr.wrapping_add(i.wrapping_mul(4));
        let v = get_u32(d, off) ^ key;
        key = key.wrapping_add(i);
        let rotated = v.rotate_right(shift);
        write_u32(d, off, rotated.wrapping_sub(i));
    }
}

fn decrypt_data4(d: &mut [u8], pos: u32) {
    let base_addr = get_u32(d, pos);
    let length = get_u32(d, pos.wrapping_add(4));
    let mut b: u8 = (((base_addr >> 8).wrapping_add(base_addr)) & 0xFF) as u8;
    let mut b2: u8 = b.wrapping_add(1);
    for i in 0..length {
        let idx = (base_addr + i) as usize;
        let b3 = d[idx];
        let b4 = b3.rotate_left(3) ^ b2;
        let b5 = b4.rotate_left(3) ^ b;
        d[idx] = b5.rotate_left(3);
        b = b.wrapping_add(1);
        b2 = b2.wrapping_add(1);
    }
}

fn decrypt_data5(d: &mut [u8], va: u32, size: u32) {
    let mut b: u8 = va as u8;
    let mut b2: u8 = b.wrapping_add(1);
    for i in 0..size {
        let idx = (va + i) as usize;
        let b3 = d[idx];
        let b4 = b3.rotate_left(2) ^ b2;
        let b5 = b4.rotate_left(2) ^ b;
        d[idx] = b5.rotate_left(2);
        b = b.wrapping_add(1);
        b2 = b2.wrapping_add(1);
    }
}

fn lfsr_keystream(out: &mut [u8]) {
    let mut state: u32 = 1;
    for byte in out.iter_mut() {
        let mut b: u8 = 0;
        for k in 0..8u32 {
            b |= ((state & 1) << k) as u8;
            state <<= 1;
            if state & 0x8000 != 0 {
                state ^= 0x8003;
            }
        }
        *byte = b;
    }
}

fn decrypt_data6(d: &mut [u8], pos: u32) {
    let len = d[(pos + 95) as usize] as usize;
    let mut ks = [0u8; 256];
    lfsr_keystream(&mut ks);
    let pos = pos as usize;
    for i in 0..len {
        d[pos + i] ^= ks[i];
    }
}

fn decrypt_data7(d: &mut [u8], pos: u32, mut key: u8) {
    let mut i: u32 = 0;
    loop {
        let idx = (pos + i) as usize;
        if d[idx] == 0 {
            break;
        }
        let mut b = d[idx];
        b = b.rotate_right(4);
        b = b.wrapping_sub(key);
        if b == 0 {
            b = 0u8.wrapping_sub(key);
        }
        d[idx] = b;
        key = key.wrapping_add(67);
        i += 1;
    }
}

fn decrypt_data8(d: &mut [u8], va: u32, size: u32, mut key: u32) {
    let blocks = size >> 4;
    for i in 0..blocks {
        let mixed = key.rotate_right(15).wrapping_add(i);
        key = mixed.wrapping_add(i);
        if i == 0 {
            continue;
        }
        let target = va
            .wrapping_add(i.wrapping_mul(16))
            .wrapping_add(mixed & 0xF);
        d[target as usize] ^= key as u8;
    }
}

fn calculate_checksum(d: &[u8], pos: u32) -> u32 {
    let offset = get_u32(d, pos);
    let length = get_u32(d, pos.wrapping_add(4));
    crc_compute(&d[offset as usize..(offset + length) as usize]) ^ length
}

// ---------------------------------------------------------------------------
// Huffman/LZ decompress (primitives.rs, verbatim minus scratch/guards)
// ---------------------------------------------------------------------------

fn decompress(
    d: &mut [u8],
    src: u32,
    mut dest: u32,
    key_offset: u32,
    s_size: u32,
    d_size: u32,
) -> bool {
    let mut bit_pos: i32 = 0;
    let mut buf = vec![0u8; s_size as usize + 3];
    let mut buf_off: u32 = 0;
    let mut src_consumed: i32 = 0;
    let mut pending: u32 = 0;
    let mut written: u32 = 0;
    let src_u = src as usize;
    let s_size_u = s_size as usize;
    buf[..s_size_u].copy_from_slice(&d[src_u..src_u + s_size_u]);

    while (src_consumed as u32) < s_size && written < d_size {
        let word = get_u32(&buf[..], buf_off) >> bit_pos;
        let tab_addr = key_offset.wrapping_add((word & 0xFF).wrapping_mul(3));
        let mut tab = get_u16(d, tab_addr);
        let bits: u8;
        if (tab & 0x8000) != 0 {
            tab &= 0x7FFF;
            bits = d[tab_addr as usize + 2];
        } else {
            let mut b2 = d[tab_addr as usize + 2];
            if b2 >= 32 {
                return false;
            }
            let mut mask: u32 = 1u32 << b2;
            b2 = b2.wrapping_add(1);
            let mut idx = (tab & 0x7FFF) as u32 + if (word & mask) != 0 { 1 } else { 0 };
            let mut t2 = get_u16(d, key_offset.wrapping_add(idx.wrapping_mul(3)));
            let mut depth = 0u32;
            while (t2 & 0x8000) == 0 {
                depth += 1;
                if depth > 64 {
                    return false;
                }
                mask <<= 1;
                b2 = b2.wrapping_add(1);
                idx = (t2 & 0x7FFF) as u32 + if (word & mask) != 0 { 1 } else { 0 };
                t2 = get_u16(d, key_offset.wrapping_add(idx.wrapping_mul(3)));
            }
            tab = t2 & 0x7FFF;
            bits = b2;
        }
        bit_pos += bits as i32;
        let advance = bit_pos / 8;
        buf_off = buf_off.wrapping_add(advance as u32);
        src_consumed += advance;
        bit_pos %= 8;

        let mode = (tab as u32) & 0x300;
        let payload = (tab as u32) & 0xFF;
        let step: u32;
        match mode {
            0 => {
                step = 1;
                d[dest as usize] = payload as u8;
            }
            0x100 => {
                step = 0;
                if pending >= 256 {
                    return false;
                }
                pending = if pending == 0 {
                    payload
                } else {
                    (pending << 8) | payload
                };
            }
            0x200 => {
                if pending == 0 {
                    pending = 1;
                }
                step = pending.wrapping_mul(payload);
                if step.wrapping_add(written) > d_size {
                    return false;
                }
                match payload {
                    1 => {
                        if dest < 1 {
                            return false;
                        }
                        let v = d[(dest as usize) - 1];
                        for k in 0..pending {
                            d[(dest + k) as usize] = v;
                        }
                    }
                    2 => {
                        if dest < 2 {
                            return false;
                        }
                        let v = get_u16(d, dest.wrapping_sub(2));
                        for k in 0..pending {
                            write_u16(d, dest.wrapping_add(k.wrapping_mul(2)), v as u32);
                        }
                    }
                    4 => {
                        if dest < 4 {
                            return false;
                        }
                        let v = get_u32(d, dest.wrapping_sub(4));
                        for k in 0..pending {
                            write_u32(d, dest.wrapping_add(k.wrapping_mul(4)), v);
                        }
                    }
                    _ => {
                        return false;
                    }
                }
                pending = 0;
            }
            _ => {
                step = payload;
                if written.wrapping_add(payload) > d_size
                    || pending.wrapping_add(payload) > written
                {
                    return false;
                }
                let back = pending.wrapping_add(payload);
                for k in 0..payload {
                    d[(dest + k) as usize] = d[(dest + k - back) as usize];
                }
                pending = 0;
            }
        }

        dest = dest.wrapping_add(step);
        written = written.wrapping_add(step);
        if bits == 0 && step == 0 {
            return false;
        }
    }
    written == d_size
}

// ---------------------------------------------------------------------------
// Bytecode VM (bytecode.rs, verbatim)
// ---------------------------------------------------------------------------

#[derive(Clone, Copy, Debug, PartialEq)]
enum Op {
    Add(u8),
    Sub(u8),
    Xor(u8),
    Rol(u32),
    Ror(u32),
    Inc,
    Dec,
}

fn apply(ops: &[Op], mut x: u8) -> u8 {
    for &op in ops {
        x = match op {
            Op::Add(n) => x.wrapping_add(n),
            Op::Sub(n) => x.wrapping_sub(n),
            Op::Xor(n) => x ^ n,
            Op::Rol(n) => x.rotate_left(n & 7),
            Op::Ror(n) => x.rotate_right(n & 7),
            Op::Inc => x.wrapping_add(1),
            Op::Dec => x.wrapping_sub(1),
        };
    }
    x
}

fn generate(data: &[u8], offset: u32) -> Option<Vec<Op>> {
    let mut pos = offset as usize;
    let mut next = move || {
        let b = data.get(pos).copied()?;
        pos += 1;
        Some(b)
    };
    let mut ops = Vec::new();
    loop {
        match next()? {
            4 => ops.push(Op::Add(next()?)),
            44 => ops.push(Op::Sub(next()?)),
            52 => ops.push(Op::Xor(next()?)),
            144 => {}
            192 => {
                let mb = next()?;
                let rm = mb & 7;
                let reg = (mb >> 3) & 7;
                let mod_ = (mb >> 6) & 3;
                if mod_ != 3 || rm != 0 {
                    return None;
                }
                let imm = next()? as u32;
                match reg {
                    0 => ops.push(Op::Rol(imm)),
                    1 => ops.push(Op::Ror(imm)),
                    _ => {
                        return None;
                    }
                }
            }
            254 => {
                let mb = next()?;
                let rm = mb & 7;
                let reg = (mb >> 3) & 7;
                let mod_ = (mb >> 6) & 3;
                if mod_ != 3 || rm != 0 {
                    return None;
                }
                match reg {
                    0 => ops.push(Op::Inc),
                    1 => ops.push(Op::Dec),
                    _ => {
                        return None;
                    }
                }
            }
            195 => return Some(ops),
            _ => {
                return None;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// PE32 advance_key (exe.rs run_pe32, verbatim)
// ---------------------------------------------------------------------------

fn advance_key(mut key: u32, iterations: u32) -> u32 {
    for m in 0..iterations {
        let bound = (m + 1).wrapping_mul(25) << 2;
        let mut n: u32 = 1;
        while n <= bound {
            key = key.wrapping_add(n);
            n += 1;
        }
    }
    key
}

// ---------------------------------------------------------------------------
// Test vector emission
// ---------------------------------------------------------------------------

fn hex(data: &[u8]) -> String {
    data.iter().map(|b| format!("{:02x}", b)).collect()
}

fn main() {
    // Deterministic pseudo-random filler (LCG), no external crates.
    let mut seed: u32 = 0x12345678;
    let mut lcg = move || {
        seed = seed.wrapping_mul(1664525).wrapping_add(1013904223);
        (seed >> 24) as u8
    };

    // --- crc32 ---
    println!("crc32_123456789 {:08x}", crc_compute(b"123456789"));
    println!(
        "crc32_chain {:08x}",
        crc_append(crc_compute(b"1234"), b"56789")
    );

    // --- decrypt_data1 (KDF) ---
    let mut file = vec![0u8; 8192];
    for b in file.iter_mut() {
        *b = lcg();
    }
    let mut info = [0u32; 8];
    decrypt_data1(&file, &mut info);
    print!("kdf_info");
    for v in info {
        print!(" {:08x}", v);
    }
    println!();

    // --- decrypt_data3 ---
    let mut d = vec![0u8; 256];
    for b in d.iter_mut() {
        *b = lcg();
    }
    write_u32(&mut d, 0, 0x40); // base_addr
    write_u32(&mut d, 4, 0x20); // length (8 dwords)
    let mut d19 = d.clone();
    decrypt_data3(&mut d19, 0, 0xA5A5_5A5A, 19);
    println!("dd3_shift19 {}", hex(&d19[0x40..0x60]));
    let mut d21 = d.clone();
    decrypt_data3(&mut d21, 0, 0xA5A5_5A5A, 21);
    println!("dd3_shift21 {}", hex(&d21[0x40..0x60]));

    // --- decrypt_data4 ---
    let mut d = vec![0u8; 256];
    for b in d.iter_mut() {
        *b = lcg();
    }
    write_u32(&mut d, 0, 0x40);
    write_u32(&mut d, 4, 0x20);
    decrypt_data4(&mut d, 0);
    println!("dd4 {}", hex(&d[0x40..0x60]));

    // --- decrypt_data5 ---
    let mut d = vec![0u8; 256];
    for b in d.iter_mut() {
        *b = lcg();
    }
    decrypt_data5(&mut d, 0x40, 0x20);
    println!("dd5 {}", hex(&d[0x40..0x60]));

    // --- LFSR keystream + decrypt_data6 ---
    let mut ks = [0u8; 96];
    lfsr_keystream(&mut ks);
    println!("lfsr96 {}", hex(&ks));
    let mut d = vec![0u8; 256];
    for b in d.iter_mut() {
        *b = lcg();
    }
    let count = d[0x40 + 95].min(95);
    d[0x40 + 95] = count;
    decrypt_data6(&mut d, 0x40);
    println!("dd6_len{:02} {}", count, hex(&d[0x40..0x40 + count as usize]));

    // --- decrypt_data7 ---
    // Encrypt a known string by hand-inverting, then decrypt it back.
    // "KERNEL32.dll" at pos 0x40, key = pos & 0xFF.
    let plain = b"KERNEL32.dll";
    let mut d = vec![0u8; 256];
    let pos = 0x40usize;
    let mut key: u8 = pos as u8;
    for (i, &p) in plain.iter().enumerate() {
        // forward (encrypt): invert of decrypt step.
        // decrypt: b = ror4(c) - key  =>  c = rol4(b + key)
        let mut b = p.wrapping_add(key);
        if b == 0 {
            b = key; // inverse of the b==0 -> -key remap
        }
        let c = b.rotate_left(4);
        d[pos + i] = c;
        key = key.wrapping_add(67);
    }
    println!("dd7_cipher {}", hex(&d[pos..pos + plain.len()]));
    decrypt_data7(&mut d, pos as u32, pos as u8);
    println!("dd7_plain {}", hex(&d[pos..pos + plain.len()]));

    // --- decrypt_data8 (PE32+ form) ---
    let mut page = vec![0u8; 4096];
    for b in page.iter_mut() {
        *b = lcg();
    }
    let mut p0 = page.clone();
    decrypt_data8(&mut p0, 0, 4096, 7 << 0);
    println!("dd8_shift0 {}", hex(&p0[..4096]));
    let mut p15 = page.clone();
    decrypt_data8(&mut p15, 0, 4096, 7 << 15);
    println!("dd8_shift15 {}", hex(&p15[..4096]));

    // --- decrypt_data8 (PE32 form) ---
    // verbatim from run_pe32's .text loop
    let dd8_pe32 = |data: &mut [u8], pa: u32, big: bool, page: u32| {
        let pk = if big {
            0x8000u32.wrapping_mul(page.wrapping_add(1))
        } else {
            page.wrapping_add(1)
        };
        let mut k = pk;
        let rk = k.rotate_right(15);
        k = rk;
        for bi in 1..256u32 {
            let rk = k.rotate_right(15);
            let ri = rk.wrapping_add(bi);
            k = ri.wrapping_add(bi);
            let tidx = pa.wrapping_add(bi.wrapping_mul(16)).wrapping_add(ri & 0xF) as usize;
            data[tidx] ^= k as u8;
        }
    };
    let mut q0 = page.clone();
    dd8_pe32(&mut q0, 0, false, 7);
    println!("dd8pe32_small {}", hex(&q0[..4096]));
    let mut q1 = page.clone();
    dd8_pe32(&mut q1, 0, true, 7);
    println!("dd8pe32_big {}", hex(&q1[..4096]));

    // --- AES ---
    // Embed a schedule: rounds=10 at key_offset+2, schedule bytes from lcg.
    let mut d = vec![0u8; 4096];
    for b in d.iter_mut() {
        *b = lcg();
    }
    let key_offset = 0x800u32;
    d[key_offset as usize + 2] = 10;
    d[key_offset as usize + 3] = 0;
    aes_decrypt(&mut d, 0x100, 0x30, key_offset);
    println!("aes_3blocks {}", hex(&d[0x100..0x130]));

    // --- calculate_checksum ---
    let mut d = vec![0u8; 512];
    for b in d.iter_mut() {
        *b = lcg();
    }
    write_u32(&mut d, 0, 0x80); // offset
    write_u32(&mut d, 4, 0x40); // length
    println!("checksum {:08x}", calculate_checksum(&d, 0));

    // --- Huffman decompress: synthetic table exercising all 4 modes ---
    // entries: idx: (u16 sym, u8 bits), 3 bytes each at key_offset 0
    let mut d = vec![0u8; 4096];
    let set_sym = |d: &mut [u8], idx: usize, sym: u16, bits: u8| {
        d[idx * 3] = (sym & 0xFF) as u8;
        d[idx * 3 + 1] = (sym >> 8) as u8;
        d[idx * 3 + 2] = bits;
    };
    set_sym(&mut d, 0, 0x8000 | 0x48, 8); // literal 'H'
    set_sym(&mut d, 1, 0x8000 | 0x69, 8); // literal 'i'
    set_sym(&mut d, 2, 0x8000 | 0x100 | 3, 8); // accumulate 3
    set_sym(&mut d, 3, 0x8000 | 0x200 | 1, 8); // run-fill width 1
    set_sym(&mut d, 4, 0x8000 | 0x300 | 2, 8); // LZ copy 2 back
    // internal node: entry 5 -> children (0,1); the stored byte is the bit
    // count accumulated so far (8 for a root entry), each level adds 1 more.
    set_sym(&mut d, 5, 0x0000, 8); // internal: children at idx 0/1
    // stream at src=0x400: symbols [0,1,2,3,4] then symbol 5 with next bit=1 -> 'i'
    let stream = [0u8, 1, 2, 3, 4, 5, 0x01];
    d[0x400..0x400 + stream.len()].copy_from_slice(&stream);
    let ok = decompress(&mut d, 0x400, 0x800, 0, stream.len() as u32, 8);
    println!("huff_ok {}", ok);
    println!("huff_out {}", hex(&d[0x800..0x808]));

    // --- bytecode VM ---
    // program: ADD AL,5 ; XOR AL,0xAA ; ROL AL,3 ; INC AL ; RET
    let prog = [0x04u8, 0x05, 0x34, 0xAA, 0xC0, 0xC0, 0x03, 0xFE, 0xC0, 0xC3];
    let ops = generate(&prog, 0).expect("generate");
    println!("bc_ops {:?}", ops);
    let mut lut = [0u8; 256];
    for i in 0..256 {
        lut[i] = apply(&ops, i as u8);
    }
    println!("bc_lut256 {}", hex(&lut));

    // --- advance_key (PE32 triangular accumulation) ---
    println!("advance_key {:08x}", advance_key(0x1234, 4));
    println!("advance_key3 {:08x}", advance_key(0xDEAD_BEEF, 3));
}
```
