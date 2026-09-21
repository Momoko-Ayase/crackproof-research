# Verification suite

This directory contains runnable reference implementations of the documented Windows transforms, fixed reference vectors, and checks for both the source files and the published Markdown snippets.

## Contents

| File | Contents |
| --- | --- |
| `primitives.py` | Rolling-key ciphers, byte-rotation ciphers, LFSR, string cipher, page scramble, on-demand page cipher, CRC-32, checksum descriptors, triangular key schedule |
| `aes_impl.py` | AES-CBC decryption with the in-buffer key schedule (tables generated from GF(2⁸) arithmetic) |
| `huffman.py` | The Huffman/LZ hybrid decompressor |
| `bytecode_vm.py` | The per-build bytecode stub decoder/interpreter, translation table, and inverse |
| `detect.py` | Content-based detection and classification of protected files |
| `rust_vectors.rs` | An independent reference port of the same algorithms, compiled to print reference vectors |
| `vectors.txt` | The vectors printed by `rust_vectors.rs` |
| `run_tests.py` | Runs 31 comparisons against the reference vectors and known answers |
| `verify_docs.py` | Executes all Windows Markdown Python blocks in English, Simplified Chinese, and Traditional Chinese, then checks their results |

## Running

Run from the repository root:

```bash
python verification/run_tests.py
python verification/verify_docs.py
```

The first command ends with `all vectors match`. The second ends with `all Windows doc snippets verified (3 languages, 48 Python blocks, 81 checks)`: nine pages, 16 Python blocks, and 27 comparisons per language. Both commands resolve paths from their script locations. The Markdown checker reports any new Python-bearing page missing from its coverage list.

The checks exercise fixed inputs. They don't establish correctness for every input, runtime loading, or commercial protection strength. Android pseudocode and non-Python examples need separate checks.

To regenerate the reference vectors, run these commands from this directory with a Rust compiler installed:

```bash
rustc -O rust_vectors.rs -o rust_vectors
./rust_vectors > vectors.txt
```

The source comparisons cover the header KDF, both XOR-ROR shifts, both byte-rotation ciphers (including the non-mutating trial read), the LFSR keystream and block decrypt, the string cipher, both page-scramble forms, the on-demand page cipher, AES-CBC over three chained blocks, the checksum descriptor, all four Huffman token modes plus an internal-node walk, the bytecode VM (op decode, 256-entry translation table, inverse-chain identity), and the triangular key schedule. `vectors.txt` contains 25 named records; some records contain several values, and the harness also checks identities and known answers.
