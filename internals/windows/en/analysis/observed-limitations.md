---
description: "Documented architectural limitations across VM checks, debug logging, demand paging, drivers, and CRC chains."
icon: triangle-exclamation
---

# Observed limitations

Static analysis and live testing across Windows build families show eight reproducible architectural limitations:

* **Prefix-only VM registry matching (`A09` & `540`):** `A09` checks vendor strings only as leading prefixes of the three BIOS/system registry values (missing hypervisors whose identifier sits at the end of `SystemBiosVersion`, or setups with `SMBIOS.reflectHost = "TRUE"`), while `540` is disabled by `monitor_control.restrict_backdoor = "TRUE"`.
* **Plaintext `%temp%` trace facility:** creating the 12-hex folder under `%temp%` causes the commercial loader itself to emit stage numbers, module addresses, missing imports, hooked APIs, and `AAA-BBB-CCC` failure coordinates in plaintext.
* **In-process demand-page servicing:** `HtdpStub2.dll`'s `KiUserExceptionDispatcher` hook decrypts faulting pages for any thread inside the process; forcing pages to fault in (and reversing optional `scribble` masks) recovers the full executable section.
* **Legacy kernel-driver attack surface:** Generation 1 (`HtsysmNT`) exposes unauthenticated ring-0 shellcode execution, and Generation 2 (`Htsysm7679`) gates its `offset < 0x1000` `EPROCESS` masked-write IOCTLs behind a reversible PID cipher (making signed builds usable as BYOVD primitives). Only Generation 3 (`0xAA02` `ObRegisterCallbacks`) avoids granting elevation primitives to usermode callers.
* **Keyless / self-contained checksum chain:** every cipher schedule, Huffman table, and bytecode stub travels inside the container, and every stage key derives from standard CRC-32 and deterministic arithmetic without external asymmetric keys, so modified payloads can have their downstream stage keys recomputed.
* **Spoofable `A03` and `A11` process markers:** `A03` checks parent executable names (`explorer.exe` / `cmd.exe`), and `A11` identifies a CrackProof host EXE via a `peC` section name or exact-case `KeRnEl32.dLl` import string rather than cryptographic host authentication.
* **Short in-memory host stamps:** builds that check an additional post-load byte marker in the host image inspect a fixed handful of bytes rather than hashing the host code.
* **Narrow usermode anti-debug surface:** live captures show commercial `410`/`520` relying on `IsDebuggerPresent` and `NtQueryInformationProcess` (with no SEH anti-debug substages inside `410`), and `A0F` scanning a fixed list of common injection DLL names.
