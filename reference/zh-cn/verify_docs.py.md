---
description: "执行三种语言的 Windows Markdown Python 片段并检查结果。"
---

# verify\_docs.py

检查器读取文档仓库的 Windows 页面，为每种语言建立独立命名空间，执行全部 Python 代码块，并对照 `verification/vectors.txt` 比较选定结果。页面覆盖列表不完整时会拒绝继续。配置的输入在每种语言的九个页面、16 个 Python 代码块上产生 27 项比对。

在文档仓库根目录运行 `python verification/verify_docs.py`。预期结束输出：`all Windows doc snippets verified (3 languages, 48 Python blocks, 81 checks)`。

检查器需要文档目录树。它检查转录与配置的向量案例；仅执行函数定义不会测试所有分支，也不能证明运行时保护行为。

```python
"""Execute the Windows Markdown Python blocks and compare their results with
the checked-in reference vectors for English and both Chinese variants.

Run from the repository root with: python verification/verify_docs.py
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "zh-cn", "zh-tw")
PYTHON_BLOCK = re.compile(r"^```python[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)

PAGES = [
    "file-structure/container-layout.md",
    "file-structure/recognition.md",
    "data-transforms/rolling-and-rotation.md",
    "data-transforms/lfsr-strings-pages.md",
    "data-transforms/checksums.md",
    "data-transforms/aes.md",
    "data-transforms/compression.md",
    "data-transforms/bytecode-transform.md",
    "runtime/page-protection.md",
]
def extract(language, namespace):
    root = REPO_ROOT / "internals" / "windows" / language
    pages = {
        path.relative_to(root).as_posix(): PYTHON_BLOCK.findall(path.read_text(encoding="utf-8"))
        for path in root.rglob("*.md")
    }
    found = {path for path, blocks in pages.items() if blocks}
    if found != set(PAGES):
        raise ValueError(
            f"{language}: Python-page coverage changed; "
            f"missing={sorted(set(PAGES) - found)}, extra={sorted(found - set(PAGES))}"
        )
    count = 0
    for page in PAGES:
        for index, block in enumerate(pages[page], 1):
            name = f"internals/windows/{language}/{page}:python-{index}"
            exec(compile(block, name, "exec"), namespace)
            count += 1
    return count


def hexs(data):
    return bytes(data).hex()


def lcg_factory(seed=0x12345678):
    state = seed

    def next_byte():
        nonlocal state
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        return state >> 24

    return next_byte


def verify_language(language, vectors):
    NS = {"__name__": "verified_windows_snippets"}
    blocks = extract(language, NS)
    failures = []
    checks = 0

    def check(name, got, want):
        nonlocal checks
        checks += 1
        if got != want:
            failures.append(name)
            print(f"FAIL {language}/{name}\n  got  {got}\n  want {want}")
        else:
            print(f"ok   {language}/{name}")

    lcg = lcg_factory()

    # Header KDF from container-layout.md.
    file_data = bytearray(lcg() for _ in range(8192))
    info = NS["header_kdf"](file_data)
    check("doc_kdf_info", [f"{x:08x}" for x in info], vectors["kdf_info"])

    # Recognition on a synthesized file.
    def build(info_vals, characteristics, opt_magic=0x20B, clr_rva=0):
        f = bytearray(8192)
        f[0x3C:0x40] = (0x80).to_bytes(4, "little")
        f[0x80:0x84] = b"PE\0\0"
        f[0x80 + 4 + 18:0x80 + 4 + 20] = characteristics.to_bytes(2, "little")
        f[0x80 + 24:0x80 + 26] = opt_magic.to_bytes(2, "little")
        dd_base = 112 if opt_magic == 0x20B else 96
        f[0x80 + 24 + dd_base + 14 * 8:0x80 + 24 + dd_base + 14 * 8 + 4] = clr_rva.to_bytes(4, "little")
        f[4096:4100] = info_vals[0].to_bytes(4, "little")
        k = info_vals[0]
        for i in range(7):
            cell = k ^ info_vals[i + 1]
            f[4100 + 4 * i:4104 + 4 * i] = cell.to_bytes(4, "little")
            k = (i * i) ^ ((k + cell - i) & 0xFFFFFFFF)
        return f

    iv = [0x11223344, 0x4E4E4F4B, 3, 4, 5, 6, 7, 8]
    check("doc_detect_native_exe", NS["detect"](build(iv, 0x0002))[0], "native-exe")
    check("doc_detect_managed_exe", NS["detect"](build(iv, 0x0002, clr_rva=0x2000))[0], "managed-exe")
    check("doc_detect_native", NS["detect"](build(iv, 0x2002))[0], "native-dll")
    check("doc_detect_managed", NS["detect"](build(iv, 0x2002, clr_rva=0x2000))[0], "managed-dll")
    check("doc_detect_pe32", NS["detect"](build(iv, 0x2002, opt_magic=0x10B, clr_rva=0x2000))[0], "managed-dll")
    check("doc_detect_pe32_exe", NS["detect"](build(iv, 0x0002, opt_magic=0x10B, clr_rva=0x2000))[0], "managed-exe")

    # Data-transform blocks.
    d = bytearray(lcg() for _ in range(256))
    NS["put_u32"](d, 0, 0x40)
    NS["put_u32"](d, 4, 0x20)
    d19 = bytearray(d)
    NS["xor_ror_dwords"](d19, 0, 0xA5A55A5A, 19)
    check("doc_dd3_19", hexs(d19[0x40:0x60]), vectors["dd3_shift19"][0])

    d = bytearray(lcg() for _ in range(256))
    NS["put_u32"](d, 0, 0x40)
    NS["put_u32"](d, 4, 0x20)
    NS["byte_rotate3"](d, 0)
    check("doc_dd4", hexs(d[0x40:0x60]), vectors["dd4"][0])

    d = bytearray(lcg() for _ in range(256))
    enc = bytearray(d)
    NS["byte_rotate2"](d, 0x40, 0x20)
    check("doc_dd5", hexs(d[0x40:0x60]), vectors["dd5"][0])
    check("doc_trial5", NS["trial_byte_rotate2"](enc, 0x40), int.from_bytes(d[0x40:0x44], "little"))

    check("doc_lfsr96", hexs(NS["lfsr_keystream"](96)), vectors["lfsr96"][0])
    d = bytearray(lcg() for _ in range(256))
    count = min(d[0x40 + 95], 95)
    d[0x40 + 95] = count
    NS["lfsr_decrypt_block"](d, 0x40)
    check("doc_dd6", hexs(d[0x40:0x40 + count]), vectors[f"dd6_len{count:02d}"][0])

    cipher = bytes.fromhex(vectors["dd7_cipher"][0])
    d = bytearray(256)
    d[0x40:0x40 + len(cipher)] = cipher
    NS["string_cipher"](d, 0x40, 0x40)
    check("doc_dd7", bytes(d[0x40:0x4C]), b"KERNEL32.dll")

    page = bytearray(lcg() for _ in range(4096))
    p0 = bytearray(page)
    NS["page_scramble"](p0, 0, 4096, 7)
    check("doc_dd8_0", hexs(p0), vectors["dd8_shift0"][0])
    p15 = bytearray(page)
    NS["page_scramble"](p15, 0, 4096, 7 << 15)
    check("doc_dd8_15", hexs(p15), vectors["dd8_shift15"][0])
    q0 = bytearray(page)
    NS["page_scramble_pe32"](q0, 0, 7, False)
    check("doc_dd8pe32_s", hexs(q0), vectors["dd8pe32_small"][0])
    q1 = bytearray(page)
    NS["page_scramble_pe32"](q1, 0, 7, True)
    check("doc_dd8pe32_b", hexs(q1), vectors["dd8pe32_big"][0])

    check("doc_crc", f"{NS['crc32'](b'123456789'):08x}", vectors["crc32_123456789"][0])

    d = bytearray(lcg() for _ in range(4096))
    d[0x800 + 2] = 10
    d[0x800 + 3] = 0
    NS["aes_decrypt"](d, 0x100, 0x30, 0x800)
    check("doc_aes", hexs(d[0x100:0x130]), vectors["aes_3blocks"][0])

    d = bytearray(4096)

    def set_sym(idx, sym, bits):
        d[idx * 3] = sym & 0xFF
        d[idx * 3 + 1] = sym >> 8
        d[idx * 3 + 2] = bits

    set_sym(0, 0x8000 | 0x48, 8)
    set_sym(1, 0x8000 | 0x69, 8)
    set_sym(2, 0x8000 | 0x100 | 3, 8)
    set_sym(3, 0x8000 | 0x200 | 1, 8)
    set_sym(4, 0x8000 | 0x300 | 2, 8)
    set_sym(5, 0x0000, 8)
    stream = bytes([0, 1, 2, 3, 4, 5, 0x01])
    d[0x400:0x400 + len(stream)] = stream
    ok = NS["decompress"](d, 0x400, 0x800, 0, len(stream), 8)
    check("doc_huff_ok", ok, True)
    check("doc_huff_out", bytes(d[0x800:0x808]), b"Hiiiiiii")

    prog = bytes([0x04, 0x05, 0x34, 0xAA, 0xC0, 0xC0, 0x03, 0xFE, 0xC0, 0xC3])
    ops = NS["generate"](prog)
    check("doc_bc_ops", ops, [("add", 5), ("xor", 170), ("rol", 3), ("inc",)])
    lut = bytes(NS["apply_ops"](ops, i) for i in range(256))
    check("doc_bc_lut", lut.hex(), vectors["bc_lut256"][0])

    check("doc_advance", f"{NS['advance_key'](0x1234, 4):08x}", vectors["advance_key"][0])

    dp_key = NS["demand_page_key"](0x1000, 0x14000000, 0xA5A55A5A)
    check("doc_dpkey", f"{dp_key:08x}", vectors["dpkey"][0])
    page = bytearray(range(64))
    NS["demand_page_decrypt"](page, dp_key)
    check("doc_dpdec64", hexs(page), vectors["dpdec64"][0])

    print(f"{language}: {len(PAGES)} pages, {blocks} Python blocks, {checks} checks, {len(failures)} failures")
    return blocks, checks, failures


def main():
    vectors = {}
    for line in (REPO_ROOT / "verification" / "vectors.txt").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if parts:
            vectors[parts[0]] = parts[1:]
    blocks = checks = failures = 0
    for language in LANGUAGES:
        language_blocks, language_checks, language_failures = verify_language(language, vectors)
        blocks += language_blocks
        checks += language_checks
        failures += len(language_failures)
    if failures:
        print(f"{failures} doc snippet comparisons failed")
        return 1
    print(f"all Windows doc snippets verified ({len(LANGUAGES)} languages, {blocks} Python blocks, {checks} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
