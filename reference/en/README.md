---
description: "Runnable Windows snippet checks and anonymized reference captures."
---

# Verification & reference

This section publishes the reference material behind [CrackProof for Windows internals](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/) in its complete, runnable form.

## Verification suite

Two checks cover the [CrackProof for Windows internals](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/) Python examples. `run_tests.py` runs 31 comparisons on the reference implementation files. `verify_docs.py` executes all 16 Python blocks across nine Windows pages in each language and runs 27 comparisons per language. The checks use fixed reference vectors and known answers; they don't prove every possible input or runtime behavior. The suite is published one page per file:

| File              | Role                                                                                                                                   |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `primitives.py`   | Rolling-key ciphers, byte rotations, LFSR, string cipher, page scramble, on-demand page cipher, CRC-32, checksums, triangular schedule |
| `aes_impl.py`     | AES-CBC decryption with the in-buffer key schedule                                                                                     |
| `huffman.py`      | Huffman/LZ hybrid decompressor                                                                                                         |
| `bytecode_vm.py`  | Per-build bytecode stub decoder/interpreter and inverse                                                                                |
| `detect.py`       | Content-based detection and classification                                                                                             |
| `run_tests.py`    | The source comparison harness (31 comparisons) |
| `verify_docs.py`  | The Markdown checker (three languages, 81 comparisons) |
| `rust_vectors.rs` | The independent port that prints reference outputs |
| `vectors.txt`     | The 25 named reference records used by the checks |

Save the reference Python files and `vectors.txt` together, then run `python run_tests.py`. It finds the vector file beside itself. Expected result: `all vectors match`.

From the documentation repository root, run:

```bash
python verification/run_tests.py
python verification/verify_docs.py
```

The Markdown checker requires the documentation tree and ends with `all Windows doc snippets verified (3 languages, 48 Python blocks, 81 checks)`. These checks cover Windows Python examples; Android pseudocode and non-Python examples need separate validation.

## Reference captures

The [sample debug logs](sample-debug-logs.md) page publishes real CrackProof debug logs captured from a protected process and then desensitized: a fully featured host EXE (page-encrypted), a native plugin DLL (bulk-decrypted only), and a managed DLL.
