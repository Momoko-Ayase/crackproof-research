---
description: >-
  Runnable snippet verification and desensitized reference material from
  protected binaries.
---

# Verification & reference

This section publishes the reference material behind [CrackProof internals](https://app.gitbook.com/o/-Lx9XUuXVg8x3nx7ouIX/s/PuKTEy2soDgSB3qfWACy/) in its complete, runnable form.

## Verification suite

Every Python snippet in the main document was verified before publication: each function's output was compared byte-for-byte against an independent reference port of the algorithms on identical inputs. The full suite — one page per file:

| File              | Role                                                                                                                                   |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `primitives.py`   | Rolling-key ciphers, byte rotations, LFSR, string cipher, page scramble, on-demand page cipher, CRC-32, checksums, triangular schedule |
| `aes_impl.py`     | AES-CBC decryption with the in-buffer key schedule                                                                                     |
| `huffman.py`      | Huffman/LZ hybrid decompressor                                                                                                         |
| `bytecode_vm.py`  | Per-build bytecode stub decoder/interpreter and inverse                                                                                |
| `detect.py`       | Content-based detection and classification                                                                                             |
| `run_tests.py`    | The comparison harness (32 vectors)                                                                                                    |
| `rust_vectors.rs` | The independent reference port that prints ground truth                                                                                |
| `vectors.txt`     | The expected outputs the harness compares against                                                                                      |

To re-run the full comparison, download the files and execute `python run_tests.py`. Expected result: `all vectors match`.

## Reference captures

Sample debug logs — real CrackProof debug logs captured from a protected process, desensitized: a fully featured host EXE (page-encrypted), a native plugin DLL (bulk-decrypted only), and a managed DLL.
