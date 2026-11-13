---
description: "/FIXED vs ASLR relocation rules, family-specific .text scramble ordering, and surgical CLR metadata overlays."
icon: cubes
---

# Relocations, page transforms, and CLR data

## Base relocations and `/FIXED` vs ASLR policy

* **Single-file 64-bit marker & 32-bit EXEs (`/FIXED`):** the packer discards base relocations and clears `DllCharacteristics`. Static reconstruction zeroes `DataDirectory[5]` and `DllCharacteristics` so the EXE loads at its preferred `ImageBase`.
* **All DLLs (32-bit and 64-bit, any family):** DLLs must remain relocatable; reconstruction preserves `DataDirectory[5]`, ensures `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` (`0x0040`) is set, and re-arms neutralized TLS relocations on PE32 DLLs.
* **Marker-less 64-bit & external-companion (`._`) builds:** preserve active ASLR flags (`DYNAMIC_BASE` / `HIGH_ENTROPY_VA`) and `DataDirectory[5]` (appending the four `DIR64` TLS relocations when companion TLS is restored).

## `.text` page-scramble (`dd8`) ordering

`dd8` must run at different points in the marker vs marker-less pipelines because marker-less builds store encrypted import strings and plaintext CLR metadata inside `.text`:

```mermaid
flowchart TB
    subgraph Marker["64-bit Marker pipeline"]
        direction LR
        M1["Recover sections"] --> M2["walk5 imports"] --> M3["Section hdrs & exports"] --> M4[".text dd8"] --> M5["Restore EP & DDs"] --> M6["CLR & TLS"]
    end
    subgraph Markerless["64-bit Marker-less pipeline"]
        direction LR
        L1["Recover sections"] --> L2["Section hdrs & exports"] --> L3["Restore EP & DDs"] --> L4[".text dd8\n(only if EP in .text)"] --> L5["DD[1] IDT imports"] --> L6["CLR & TLS"]
    end
```

On marker-less builds, running `dd8` after section-header and EP/directory restoration (gated on `AddressOfEntryPoint` falling inside `.text`) and **before** `DD[1]` import-name decryption and CLR overlay prevents `dd8` from re-scrambling freshly decrypted import strings or corrupting overlaid `COR20`/`BSJB` bytes.

## Surgical CLR metadata restoration

Managed CrackProof builds encrypt IL method bodies inside section payloads while keeping ECMA-335 metadata structures unencrypted in the outer file or companion stub:

* **Single-file marker-less 64-bit:** overlays the `COR20` header (`cb == 0x48`) and `BSJB` metadata stream at their RVAs after `dd8`.
* **Single-file marker 64-bit:** overlays `COR20`, `BSJB` metadata, and `COR20.Resources` (`+0x18`).
* **Managed companion (`._`) DLLs:** overlays `COR20` (`0x48` bytes) from the stub PE together with all seven referenced sub-ranges when nonzero: `MetaData` (`BSJB`, required), `Resources`, `StrongNameSignature`, `CodeManagerTable`, `VTableFixups` (plus each referenced slot array), `ExportAddressTableJumps`, and `ManagedNativeHeader`.

{% hint style="warning" %}
**Never copy an entire CLR-bearing section after section recovery.** IL method bodies share `.text` with `COR20` and `BSJB` and are recovered by `walk4` + `dd8`; overwriting the whole section from the protected file or stub replaces decrypted method bodies with ciphertext. (Only the older dedicated 64-bit DLL pipeline pre-fills the CLR section *before* `walk4` writes recovered method bodies on top of it.)
{% endhint %}

If `DataDirectory[14]` points to a zeroed `COR20` header (`cb == 0`) with no valid preserved copy, `DataDirectory[14]` is cleared. Unity IL2CPP titles pack native `GameAssembly.dll` without CLR headers and obfuscate `global-metadata.dat` separately; see [il2cpp metadata obfuscation](../../analysis/il2cpp-metadata.md).
