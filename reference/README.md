---
description: "The runnable verification suite behind the document's Python snippets, plus desensitized reference material captured from real protected binaries."
---

# Verification & reference

This section publishes the reference material behind [CrackProof internals](https://launchcore.gitbook.io/crackproof-research/docs) in its complete, runnable form.

## Verification suite

Every Python snippet in the main document was verified before publication: each function's output was compared byte-for-byte against an independent reference port of the algorithms on identical inputs. The full suite — one page per file:

| File | Role |
| --- | --- |
| [`primitives.py`](primitives.md) | Rolling-key ciphers, byte rotations, LFSR, string cipher, page scramble, CRC-32, checksums, triangular schedule |
| [`aes_impl.py`](aes-impl.md) | AES-CBC decryption with the in-buffer key schedule |
| [`huffman.py`](huffman.md) | Huffman/LZ hybrid decompressor |
| [`bytecode_vm.py`](bytecode-vm.md) | Per-build bytecode stub decoder/interpreter and inverse |
| [`detect.py`](detect.md) | Content-based detection and classification |
| [`run_tests.py`](run-tests.md) | The comparison harness (30 vectors) |
| [`rust_vectors.rs`](rust-vectors.md) | The independent reference port that prints ground truth |
| [`vectors.txt`](vectors.md) | The expected outputs the harness compares against |

To re-run the full comparison, download the files and execute `python run_tests.py`. Expected result: `all vectors match`.

## Reference captures

[Sample debug logs](debug-logs.md) — real CrackProof debug logs captured from a protected process, desensitized: a fully featured host EXE (page-encrypted), a native plugin DLL (bulk-decrypted only), and a managed DLL.
