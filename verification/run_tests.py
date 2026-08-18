"""Cross-check every Python snippet against the vectors printed by the
verbatim Rust port (rust_vectors.rs -> vectors.txt). Exit 0 = all match."""

import sys

import primitives as P
import aes_impl
import huffman
import bytecode_vm


def lcg_factory(seed=0x12345678):
    state = seed

    def next_byte():
        nonlocal state
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        return state >> 24

    return next_byte


def load_vectors(path):
    out = {}
    for line in open(path):
        parts = line.split()
        if parts:
            out[parts[0]] = parts[1:]
    return out


def hexs(data):
    return bytes(data).hex()


FAILURES = []


def check(name, got, want):
    if got != want:
        FAILURES.append(name)
        print(f"FAIL {name}\n  got  {got}\n  want {want}")
    else:
        print(f"ok   {name}")


def main():
    v = load_vectors("vectors.txt")
    lcg = lcg_factory()

    # --- crc32 (also cross-check against the zlib standard CRC) ---
    import zlib
    check("crc32_123456789", f"{P.crc32(b'123456789'):08x}", v["crc32_123456789"][0])
    check("crc32_zlib_agrees", f"{zlib.crc32(b'123456789'):08x}", v["crc32_123456789"][0])
    chained = P.crc32_append(P.crc32(b"1234"), b"56789")
    check("crc32_chain", f"{chained:08x}", v["crc32_chain"][0])

    # --- header KDF ---
    file_data = bytearray(lcg() for _ in range(8192))
    info = P.header_kdf(file_data)
    check("kdf_info", [f"{x:08x}" for x in info], v["kdf_info"])

    # --- xor_ror_dwords (decrypt_data3), shifts 19 and 21 ---
    d = bytearray(lcg() for _ in range(256))
    P.put_u32(d, 0, 0x40)
    P.put_u32(d, 4, 0x20)
    d19 = bytearray(d)
    P.xor_ror_dwords(d19, 0, 0xA5A55A5A, 19)
    check("dd3_shift19", hexs(d19[0x40:0x60]), v["dd3_shift19"][0])
    d21 = bytearray(d)
    P.xor_ror_dwords(d21, 0, 0xA5A55A5A, 21)
    check("dd3_shift21", hexs(d21[0x40:0x60]), v["dd3_shift21"][0])

    # --- byte_rotate3 (decrypt_data4) ---
    d = bytearray(lcg() for _ in range(256))
    P.put_u32(d, 0, 0x40)
    P.put_u32(d, 4, 0x20)
    P.byte_rotate3(d, 0)
    check("dd4", hexs(d[0x40:0x60]), v["dd4"][0])

    # --- byte_rotate2 (decrypt_data5) ---
    d = bytearray(lcg() for _ in range(256))
    enc = bytearray(d)  # keep the encrypted state for the trial reads
    P.byte_rotate2(d, 0x40, 0x20)
    check("dd5", hexs(d[0x40:0x60]), v["dd5"][0])

    # trial read matches the mutating pass
    for off in (0x40, 0x44, 0x5C):
        want = int.from_bytes(d[off:off + 4], "little")
        check(f"trial5_{off:x}", P.trial_byte_rotate2(enc, off), want)

    # --- LFSR keystream + block decrypt ---
    check("lfsr96", hexs(P.lfsr_keystream(96)), v["lfsr96"][0])
    d = bytearray(lcg() for _ in range(256))
    count = min(d[0x40 + 95], 95)
    d[0x40 + 95] = count
    P.lfsr_decrypt_block(d, 0x40)
    check("dd6", hexs(d[0x40:0x40 + count]), v[f"dd6_len{count:02d}"][0])

    # --- string cipher (decrypt_data7) ---
    cipher = bytes.fromhex(v["dd7_cipher"][0])
    d = bytearray(256)
    d[0x40:0x40 + len(cipher)] = cipher
    P.string_cipher(d, 0x40, 0x40)
    check("dd7_plain", hexs(d[0x40:0x40 + len(cipher)]), v["dd7_plain"][0])
    check("dd7_is_kernel32", bytes(d[0x40:0x4C]), b"KERNEL32.dll")

    # --- page scramble (PE32+ form) ---
    page = bytearray(lcg() for _ in range(4096))
    p0 = bytearray(page)
    P.page_scramble(p0, 0, 4096, 7 << 0)
    check("dd8_shift0", hexs(p0), v["dd8_shift0"][0])
    p15 = bytearray(page)
    P.page_scramble(p15, 0, 4096, 7 << 15)
    check("dd8_shift15", hexs(p15), v["dd8_shift15"][0])

    # --- page scramble (PE32 form) ---
    q0 = bytearray(page)
    P.page_scramble_pe32(q0, 0, 7, False)
    check("dd8pe32_small", hexs(q0), v["dd8pe32_small"][0])
    q1 = bytearray(page)
    P.page_scramble_pe32(q1, 0, 7, True)
    check("dd8pe32_big", hexs(q1), v["dd8pe32_big"][0])

    # --- AES-CBC ---
    d = bytearray(lcg() for _ in range(4096))
    d[0x800 + 2] = 10
    d[0x800 + 3] = 0
    aes_impl.aes_decrypt(d, 0x100, 0x30, 0x800)
    check("aes_3blocks", hexs(d[0x100:0x130]), v["aes_3blocks"][0])

    # --- calculate_checksum ---
    d = bytearray(lcg() for _ in range(512))
    P.put_u32(d, 0, 0x80)
    P.put_u32(d, 4, 0x40)
    check("checksum", f"{P.calculate_checksum(d, 0):08x}", v["checksum"][0])

    # --- Huffman/LZ decompress ---
    d = bytearray(4096)

    def set_sym(idx, sym, bits):
        d[idx * 3] = sym & 0xFF
        d[idx * 3 + 1] = sym >> 8
        d[idx * 3 + 2] = bits

    set_sym(0, 0x8000 | 0x48, 8)  # literal 'H'
    set_sym(1, 0x8000 | 0x69, 8)  # literal 'i'
    set_sym(2, 0x8000 | 0x100 | 3, 8)  # accumulate 3
    set_sym(3, 0x8000 | 0x200 | 1, 8)  # run fill, width 1
    set_sym(4, 0x8000 | 0x300 | 2, 8)  # LZ copy, 2 back
    set_sym(5, 0x0000, 8)  # internal node -> children 0/1
    stream = bytes([0, 1, 2, 3, 4, 5, 0x01])
    d[0x400:0x400 + len(stream)] = stream
    ok = huffman.decompress(d, 0x400, 0x800, 0, len(stream), 8)
    check("huff_ok", str(ok).lower(), v["huff_ok"][0])
    check("huff_out", hexs(d[0x800:0x808]), v["huff_out"][0])
    check("huff_decodes_to", bytes(d[0x800:0x808]), b"Hiiiiiii")

    # --- bytecode VM ---
    prog = bytes([0x04, 0x05, 0x34, 0xAA, 0xC0, 0xC0, 0x03, 0xFE, 0xC0, 0xC3])
    ops = bytecode_vm.generate(prog)
    check("bc_ops", ops, [("add", 5), ("xor", 170), ("rol", 3), ("inc",)])
    lut = bytecode_vm.build_translation_table(ops)
    check("bc_lut256", lut.hex(), v["bc_lut256"][0])
    # inverse chain restores identity
    inv = bytecode_vm.inverse_ops(ops)
    check("bc_inverse_identity",
          all(bytecode_vm.apply_ops(inv, bytecode_vm.apply_ops(ops, i)) == i for i in range(256)),
          True)

    # --- advance_key ---
    check("advance_key", f"{P.advance_key(0x1234, 4):08x}", v["advance_key"][0])
    check("advance_key3", f"{P.advance_key(0xDEADBEEF, 3):08x}", v["advance_key3"][0])

    # --- on-demand page cipher ---
    dp_key = P.demand_page_key(0x1000, 0x14000000, 0xA5A55A5A)
    check("dpkey", f"{dp_key:08x}", v["dpkey"][0])
    page = bytearray(range(64))
    P.demand_page_decrypt(page, dp_key)
    check("dpdec64", hexs(page), v["dpdec64"][0])

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES: {FAILURES}")
        return 1
    print("all vectors match")
    return 0


if __name__ == "__main__":
    sys.exit(main())
