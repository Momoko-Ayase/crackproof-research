---
description: "Weaknesses and failure modes observed in specific protection mechanisms and build families."
---

# Observed limitations

## Observed weaknesses

For completeness and future research, the mechanisms that demonstrably fall short:

**The VM checks are bypassable by configuration alone.** The registry check matches vendor strings only at the *start* of the BIOS/product values, while at least one major hypervisor places its marker at the *end* of its BIOS version. Setting `SMBIOS.reflectHost = "TRUE"` hides it entirely. The VMware backdoor probe is neutralized by `monitor_control.restrict_backdoor = "TRUE"` (and by not installing guest tools), and other hypervisors allow overriding SMBIOS strings directly.

**The debug log is a self-documenting loader.** The status-code design that helps the vendor's support also hands the analyst a stage-by-stage execution trace and a 2-byte search pattern per stage. The mailslot channel is encrypted, but the file log isn't.

**Page encryption yields to in-process readers.** The demand-decrypt handler services faults from any thread in the same process, so a helper inside the process can touch every page and copy the decrypted bytes. The anti-dump scribble is reversible, and on builds where it's disabled the pages are clean.

**The kernel drivers weaken the host.** Generation 1 exposes unauthenticated kernel shellcode execution to any process. Generation 2's PID-encryption "authentication" grants its `EPROCESS`-write primitive to any program that reproduces it (a signed BYOVD), and the Protected Process flag it sets can be toggled off with kernel-level access or absorbed by injecting before it's set. Only generation 3 avoids granting attackers new powers.

**The tamper-evidence chain is fully recomputable.** Every transform in the container is reversible (XOR chains, rotations, a permutation bytecode, CBC-mode AES with an embedded schedule) and every checksum is a standard CRC-32 over knowable bytes. Nothing in the design requires a secret held outside the file. Consequently the checksum chain detects naive patching but can't prevent it: an analyst who modifies the payload can recompute every chained key and re-embed the result, and the loader will accept it. The chain raises the cost of modification; it doesn't bound it.

**Process-policy checks are coarse.** The parent-process policy (`A03`) is satisfied by launching from an approved parent, and the DLL host check (`A11`) keys on artifacts (a `peC` section, mixed-case `KeRnEl32.dLl` imports) that identify only unmodified hosts.

**Host-module stamps are short.** Some builds add an extra check that the host process still carries a small in-memory CrackProof marker after load. The marker is a few bytes, not a checksum over the reconstructed image, so changing those bytes is enough for the check to accept an otherwise foreign host.

**Usermode anti-debug is a short list.** The `410`/`520` path has been observed to use `IsDebuggerPresent` and `NtQueryInformationProcess`. The injected-DLL sweep (`A0F`) keys on a short list of well-known injection points and doesn't cover every common forwarded-export name.

None of these make the protection trivial. The layered design still costs real effort to analyze end-to-end, but each is a documented, reproducible gap rather than a theoretical one.
