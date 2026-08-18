# Verification suite

This directory contains the complete, runnable form of every Python snippet in the documentation, plus the harness that proves them correct.

## Contents

| File | Contents |
| --- | --- |
| `primitives.py` | Rolling-key ciphers, byte-rotation ciphers, LFSR, string cipher, page scramble, on-demand page cipher, CRC-32, checksum descriptors, triangular key schedule |
| `aes_impl.py` | AES-CBC decryption with the in-buffer key schedule (tables generated from GF(2⁸) arithmetic) |
| `huffman.py` | The Huffman/LZ hybrid decompressor |
| `bytecode_vm.py` | The per-build bytecode stub decoder/interpreter, translation table, and inverse |
| `detect.py` | Content-based detection and classification of protected files |
| `rust_vectors.rs` | An independent reference port of the same algorithms, compiled to print ground-truth vectors |
| `vectors.txt` | The vectors printed by `rust_vectors.rs` |
| `run_tests.py` | Replays every scenario in Python and compares byte-for-byte with the Rust vectors |

## Running

```bash
python run_tests.py        # expected: "all vectors match"
```

To regenerate the ground-truth vectors (requires a Rust compiler):

```bash
rustc -O rust_vectors.rs -o rust_vectors
./rust_vectors > vectors.txt
```

The test scenarios cover: the header KDF, both XOR-ROR shifts, both byte-rotation ciphers (including the non-mutating trial read), the LFSR keystream and block decrypt, the string cipher, both page-scramble forms, the on-demand page cipher, AES-CBC over three chained blocks, the checksum descriptor, all four Huffman token modes plus an internal-node walk, the bytecode VM (op decode, 256-entry translation table, inverse-chain identity), and the triangular key schedule — 32 vectors in total.
