# Table of contents

* [CrackProof for Windows internals](README.md)

## File structure

* [Overview](file-structure/file-format.md)
* [Container and encrypted header](file-structure/container-layout.md)
* [Recognition and build families](file-structure/recognition.md)
* [Section data and companion files](file-structure/companion-layout.md)

## Data transforms

* [Overview](data-transforms/data-transforms.md)
* [Rolling-key and rotation ciphers](data-transforms/rolling-and-rotation.md)
* [LFSR, string, and page transforms](data-transforms/lfsr-strings-pages.md)
* [Checksums and key progression](data-transforms/checksums.md)
* [AES-CBC layer](data-transforms/aes.md)
* [Huffman and LZ compression](data-transforms/compression.md)
* [Per-build byte transform](data-transforms/bytecode-transform.md)

## Loading and PE repair

* [Loading and section recovery](loading-and-pe-repair/loading/README.md)
  * [Stage chain and marker layout](loading-and-pe-repair/loading/stage-chain.md)
  * [PE32, DLL, and marker-less layouts](loading-and-pe-repair/loading/layout-variants.md)
  * [Structural discovery and validation](loading-and-pe-repair/loading/discovery-validation.md)
* [PE reconstruction](loading-and-pe-repair/pe-reconstruction/README.md)
  * [Headers, sections, and zero-fill ranges](loading-and-pe-repair/pe-reconstruction/memory-image.md)
  * [Imports, TLS, and exports](loading-and-pe-repair/pe-reconstruction/imports-tls-exports.md)
  * [Relocations, page transforms, and CLR data](loading-and-pe-repair/pe-reconstruction/relocations-managed.md)

## Runtime

* [Overview](runtime/runtime.md)
* [Startup sequence and status reporting](runtime/startup-status.md)
* [Environment and anti-analysis checks](runtime/environment-checks.md)
* [Page protection and loader code](runtime/page-protection.md)
* [Manually mapped helper modules](runtime/mapped-modules.md)
* [Htsysm kernel components](runtime/kernel-components.md)

## Analysis

* [Overview](analysis/analysis.md)
* [Analysis workflow](analysis/workflow.md)
* [Observed limitations](analysis/observed-limitations.md)
* [il2cpp metadata obfuscation](analysis/il2cpp-metadata.md)
* [Constants and offsets](analysis/constants.md)
