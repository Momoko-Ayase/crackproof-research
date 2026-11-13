---
description: "Usermode anti-analysis, native-bridge, ptrace, memory-read, and APK signature checks on Android."
icon: user-shield
---

# Environment and integrity checks

Unlike the Windows family, CrackProof on Android runs entirely in usermode without a kernel driver. Its probes execute across Stage 1, Stage 2, and the worker modules cataloged in [Runtime modules](modules.md) while nested streams unpack.

## Process and ABI translation checks

* **Self-mapping and environment:** Stage 1 parses `/proc/self/maps` to locate its backing ELF; Stage 2 retains a maps context and inspects `/proc/self/environ`.
* **ARM-on-x86 binary translation (NativeBridge):** probes check for `/system/lib/libhoudini.so` and `/system/lib64/arm64/nb/` to detect ARM-on-x86 translation layers rather than native AArch64 execution.
* **Filesystem and libc checks:** module `0x8F` inspects `/proc/self/cmdline`, `uid`/`gid`/`tid`, and file ownership/permissions; module `0x60` scans system library directories and runtime paths; module `0x20` validates target ELF headers, `/proc/self/maps`, and the active `libc` mapping.

## Helper process and `PTRACE_SEIZE`

Observed IL2CPP builds `fork` a companion process after ART and VM libraries are initialized but before `dlopen` loads the protected `.so`. The child attaches to the parent with `PTRACE_SEIZE | PTRACE_O_EXITKILL`, occupying the kernel `ptrace` attachment slot and terminating the app if either process exits. Because the `fork` happens before the protected `.so` is loaded, the library never appears in `/proc/<child>/maps`.

## `/proc/<pid>/mem` monitoring vs page permissions

Opening and reading `/proc/<pid>/mem` on observed builds terminates the process within seconds; reading `/proc/<pid>/maps`, `cmdline`, or `status`, or reading memory via `process_vm_readv`, did not trigger termination on those builds. Once `0x9B` finishes restoring segments, executable pages remain readable (`PROT_READ | PROT_EXEC`); Android builds do not install a `PAGE_NOACCESS` demand-fault page cipher.

## APK signatures and network time

Module `0x40` verifies `base.apk` and split APKs in descending scheme order: APK Signature Scheme v3.1, then v3, then v2, then JAR signing (v1). Module `0x02` queries an NTP server over UDP port 123 and compares the returned timestamp against a configured bound. Module `0x69` spawns a short-lived child probe and checks its wait status.

## Absence from linker module lists

Stage 2 interpreters and worker modules live in anonymous `mmap` regions (frequently `RWX` during setup) and can zero or overwrite themselves after completing their callbacks. Like [manually mapped helper DLLs](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/runtime/mapped-modules) on Windows, none of these modules appear in Bionic's `dl_iterate_phdr` or `soinfo` lists.
