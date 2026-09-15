---
description: "Observed Android environment, integrity, and dump-related checks at load time."
---

# Environment and integrity checks

Windows builds combine usermode probes with optional kernel support. The Android family stays in usermode. The checks on this page are taken from stage 1, stage 2, and the modules listed on [Runtime modules](modules.md). They run while these nested streams are still materializing, not after a restored ELF is already in place.

## Process and translation environment

Stage 1 already walks `/proc/self/maps` to find its own file. Stage 2 keeps a maps context and also looks at `/proc/self/environ`. One observed probe tests for an x86-on-ARM translation layer by looking for paths under `/system/lib/libhoudini.so` and `/system/lib64/arm64/nb/`. A host that's translating ARM code, rather than running AArch64 natively, is therefore a distinct environment from the one the loader expects.

Module `0x8F` reads `/proc/self/cmdline`, queries uid/gid/tid, and checks the owner and mode of a path. Module `0x60` scans system library directories, the process environment, and runtime paths. Module `0x20` validates a target path, an ELF header, `/proc/self/maps`, and a libc mapping.

## Second process and ptrace

Observed IL2CPP libraries fork a helper process after ART has started and the VM modules are mapped, but before the protected library itself is loaded. The child seizes the parent with `PTRACE_SEIZE` and `PTRACE_O_EXITKILL`. That occupies the ptrace slot and ties the two process lifetimes together. The child's maps therefore never contain the protected library.

## Memory visibility

Opening and reading `/proc/<pid>/mem` has been observed to kill the process within a few seconds. Reads of `maps`, `cmdline`, and `status` don't. `process_vm_readv` produced no such reaction on the same builds. Once restoration has finished, executable pages stay readable. There's no Windows-style `PAGE_NOACCESS` re-encryption of demand-faulted code.

## Package and time

Module `0x40` checks `base.apk` and sibling split APKs. The observed signature order is v3.1, then v3, then v2, then JAR/v1. Module `0x02` sends a UDP port-123 time query and compares the reply with a configured threshold. Module `0x69` forks a child probe and waits for its exit status.

## What is absent

No Htsysm-class kernel driver appears on this path. Stage 2 modules are ordinary usermode images, often in private RWX regions, and they can wipe or rewrite themselves after they run. Their absence from the dynamic linker's module list is the same kind of gap that [manually mapped helpers](https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/runtime/mapped-modules) create on Windows.
