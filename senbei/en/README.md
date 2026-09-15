---
description: "A static unpacker for CrackProof-protected Windows PE files and Android AArch64 shared libraries."
---

# Senbei

Senbei is a static unpacker for programs protected by CrackProof. Point it at a file, an app package, or a folder, and it writes restored copies without launching or attaching to the protected program.

Senbei reads the protected bytes, replays the protection algorithm, validates the result against structural checks, and writes the recovered image. A candidate that fails validation is rejected, never emitted as a silently damaged binary.

Supported inputs:

* Protected Windows `.exe` and `.dll` files — 64-bit and 32-bit, native and managed — including external `.exe._` and `.dll._` companion payloads
* `global-metadata.dat` files with supported method-token layouts
* Protected Android `.so` files, standalone or inside `.apk`, `.apks`, and `.xapk` packages

The protection formats and runtime behavior behind these inputs are documented in [CrackProof for Windows internals](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/) and [CrackProof for Android SO internals](https://app.gitbook.com/s/fcBZibCo72OSh5jVcKoo/).

## In this section

| Page                      | What it covers                                              |
| ------------------------- | ----------------------------------------------------------- |
| [Usage](usage.md)         | Running the command-line tool: targets, flags, and exit codes |
| [Design](design.md)       | How the workspace and the restoration pipelines are organized |
| [Development](development.md) | Building, testing, and contributing                      |

## Browser app

The same engine also runs in the browser, compiled to WebAssembly. Files are processed locally and never uploaded. The browser build handles single files; folder scanning and Android package orchestration stay in the command-line tool.
